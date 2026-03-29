#!/usr/bin/env python3
"""Journal abbreviation lookup tool with multi-source cascade.

Sources (in priority order):
1. JabRef CSV cache (local, ~25K journals, instant)
2. AbbrevISO API (forward only, algorithmic ISO 4)
3. NLM Catalog / Entrez (bidirectional, biomedical journals)

Usage:
    python3 jabbrv.py lookup "Nature Medicine"
    python3 jabbrv.py abbrev "Nature Medicine"
    python3 jabbrv.py expand "Nat. Med."
    python3 jabbrv.py search "J Biol"
    python3 jabbrv.py bib refs.bib
    python3 jabbrv.py batch journals.txt
    python3 jabbrv.py update-cache
"""

import csv
import io
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).parent / "cache"

# JabRef CSV files on GitHub (CC0 licensed)
JABREF_BASE = "https://raw.githubusercontent.com/JabRef/abbrv.jabref.org/main/journals"
JABREF_FILES = [
    # ISO 4 (dotted) sources first — these take priority
    "journal_abbreviations_general.csv",
    "journal_abbreviations_lifescience.csv",
    "journal_abbreviations_acs.csv",
    "journal_abbreviations_ams.csv",
    "journal_abbreviations_astronomy.csv",
    "journal_abbreviations_dainst.csv",
    "journal_abbreviations_geology_physics.csv",
    "journal_abbreviations_geology_physics_variations.csv",
    "journal_abbreviations_ieee.csv",
    "journal_abbreviations_ieee_strings.csv",
    "journal_abbreviations_mathematics.csv",
    "journal_abbreviations_mechanical.csv",
    "journal_abbreviations_meteorology.csv",
    "journal_abbreviations_sociology.csv",
    "journal_abbreviations_ubc.csv",
    # MEDLINE (no dots) sources last — used as fallback
    "journal_abbreviations_entrez.csv",
    "journal_abbreviations_medicus.csv",
]

# Track files that failed download to avoid retrying
_failed_files = set()

# Rate limiting
_last_abbreviso_time = 0
_last_nlm_time = 0
_ABBREVISO_GAP = 1.0
_NLM_GAP = 0.35  # ~3 req/sec


def _fetch(url, timeout=15):
    """Fetch URL with User-Agent header."""
    req = Request(url, headers={"User-Agent": "jabbrv/1.0 (journal-abbrev-skill)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _fetch_json(url, timeout=15):
    """Fetch URL and parse as JSON."""
    return json.loads(_fetch(url, timeout))


# --- Cache Management ---


def ensure_cache():
    """Download JabRef CSV files if not present."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for fname in JABREF_FILES:
        fpath = CACHE_DIR / fname
        if fpath.exists() or fname in _failed_files:
            continue
        url = f"{JABREF_BASE}/{fname}"
        print(f"  Downloading {fname}...", file=sys.stderr)
        try:
            data = _fetch(url, timeout=30)
            fpath.write_text(data, encoding="utf-8")
            downloaded += 1
        except (HTTPError, URLError) as e:
            _failed_files.add(fname)
            print(f"  Warning: failed to download {fname}: {e}", file=sys.stderr)
    if downloaded:
        print(f"  Downloaded {downloaded} cache files.", file=sys.stderr)


def load_cache():
    """Parse all JabRef CSVs into lookup dicts."""
    ensure_cache()
    full_to_abbrev = {}  # normalized_full -> (full, abbrev)
    abbrev_to_full = {}  # normalized_abbrev -> (abbrev, full)

    for fname in JABREF_FILES:
        fpath = CACHE_DIR / fname
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8", errors="replace")
        # JabRef CSVs use comma delimiter with quoted fields
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if len(row) < 2 or row[0].startswith("#"):
                continue
            full = row[0].strip()
            abbrev = row[1].strip()
            if not full or not abbrev:
                continue
            nf = _normalize(full)
            na = _normalize(abbrev)
            if nf not in full_to_abbrev:
                full_to_abbrev[nf] = (full, abbrev)
            if na not in abbrev_to_full:
                abbrev_to_full[na] = (abbrev, full)

    return full_to_abbrev, abbrev_to_full


def _normalize(s):
    """Normalize for case-insensitive matching."""
    s = s.lower().strip()
    s = re.sub(r"^the\s+", "", s)
    s = s.replace("&", "and")
    s = re.sub(r"\s+", " ", s)
    return s


# Singleton cache
_cache = None


def _get_cache():
    global _cache
    if _cache is None:
        _cache = load_cache()
    return _cache


# --- Local Lookup ---


def lookup_local(query):
    """Look up in JabRef cache. Returns dict with result or None."""
    full_to_abbrev, abbrev_to_full = _get_cache()
    nq = _normalize(query)

    # Try forward (full -> abbrev)
    if nq in full_to_abbrev:
        full, abbrev = full_to_abbrev[nq]
        return {
            "query": query,
            "full": full,
            "abbreviation": abbrev,
            "direction": "abbreviate",
            "source": "JabRef",
        }

    # Try reverse (abbrev -> full)
    if nq in abbrev_to_full:
        abbrev, full = abbrev_to_full[nq]
        return {
            "query": query,
            "full": full,
            "abbreviation": abbrev,
            "direction": "expand",
            "source": "JabRef",
        }

    return None


def fuzzy_search(query, n=10):
    """Fuzzy search against cache keys. Supports multi-word queries (all terms must match)."""
    full_to_abbrev, abbrev_to_full = _get_cache()
    nq = _normalize(query)
    terms = nq.split()
    results = []

    def _matches(text):
        return all(t in text for t in terms)

    # Search in full names
    for nf, (full, abbrev) in full_to_abbrev.items():
        if _matches(nf):
            results.append({"full": full, "abbreviation": abbrev, "source": "JabRef"})

    # Search in abbreviations
    for na, (abbrev, full) in abbrev_to_full.items():
        if _matches(na):
            if not any(r["full"] == full for r in results):
                results.append({"full": full, "abbreviation": abbrev, "source": "JabRef"})

    # Sort: exact prefix matches first, then by length
    results.sort(key=lambda r: (not _normalize(r["full"]).startswith(nq), len(r["full"])))
    return results[:n]


# --- AbbrevISO API ---


def lookup_abbreviso(name):
    """Look up abbreviation via AbbrevISO (forward only)."""
    global _last_abbreviso_time
    elapsed = time.time() - _last_abbreviso_time
    if elapsed < _ABBREVISO_GAP:
        time.sleep(_ABBREVISO_GAP - elapsed)

    encoded = quote(name, safe="")
    url = f"https://abbreviso.toolforge.org/a/{encoded}"
    try:
        _last_abbreviso_time = time.time()
        result = _fetch(url).strip()
        if result and result != name:
            return {
                "query": name,
                "full": name,
                "abbreviation": result,
                "direction": "abbreviate",
                "source": "AbbrevISO",
                "standard": "ISO 4",
            }
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  AbbrevISO error: {e}", file=sys.stderr)
    return None


# --- NLM Catalog (Entrez) ---


def lookup_nlm(query, direction="abbreviate"):
    """Look up via NLM Catalog. direction: 'abbreviate' or 'expand'."""
    global _last_nlm_time
    elapsed = time.time() - _last_nlm_time
    if elapsed < _NLM_GAP:
        time.sleep(_NLM_GAP - elapsed)

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    if direction == "expand":
        # Search by abbreviation in the TA (Title Abbreviation) field
        term = f'"{query}"[ta]'
    else:
        # Search by full title
        term = f'"{query}"[All Fields]'

    search_url = f"{base}/esearch.fcgi?db=nlmcatalog&term={quote(term)}&retmax=3&retmode=json"
    try:
        _last_nlm_time = time.time()
        data = _fetch_json(search_url)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return None

        # Fetch details
        elapsed = time.time() - _last_nlm_time
        if elapsed < _NLM_GAP:
            time.sleep(_NLM_GAP - elapsed)
        _last_nlm_time = time.time()

        fetch_url = f"{base}/efetch.fcgi?db=nlmcatalog&id={ids[0]}&retmode=xml"
        xml_text = _fetch(fetch_url)
        root = ET.fromstring(xml_text)

        # Extract title and abbreviation
        title_el = root.find(".//TitleMain/Title")
        abbrev_el = root.find(".//MedlineTA")

        if title_el is not None and abbrev_el is not None:
            full = title_el.text.strip().rstrip(".")
            abbrev = abbrev_el.text.strip()
            return {
                "query": query,
                "full": full,
                "abbreviation": abbrev,
                "direction": direction,
                "source": "NLM Catalog",
                "standard": "MEDLINE",
            }
    except (HTTPError, URLError, TimeoutError, ET.ParseError) as e:
        print(f"  NLM error: {e}", file=sys.stderr)
    return None


# --- Cascade Functions ---


def abbreviate(name):
    """Full name -> abbreviation. Cascade: local -> AbbrevISO -> NLM."""
    # 1. Local cache
    result = lookup_local(name)
    if result and result["direction"] == "abbreviate":
        return result

    # 2. AbbrevISO API
    result = lookup_abbreviso(name)
    if result:
        return result

    # 3. NLM Catalog
    result = lookup_nlm(name, direction="abbreviate")
    if result:
        return result

    return None


def expand(abbrev):
    """Abbreviation -> full name. Cascade: local -> NLM."""
    # 1. Local cache
    result = lookup_local(abbrev)
    if result and result["direction"] == "expand":
        return result

    # Also check if it's a known full name
    result = lookup_local(abbrev)
    if result:
        return result

    # 2. NLM Catalog
    result = lookup_nlm(abbrev, direction="expand")
    if result:
        return result

    return None


def auto_lookup(query):
    """Auto-detect direction and look up."""
    # Heuristic: if query contains periods or very short words, likely an abbreviation
    words = query.split()
    has_periods = "." in query
    avg_word_len = sum(len(w.rstrip(".")) for w in words) / max(len(words), 1)

    if has_periods or (len(words) > 1 and avg_word_len < 4):
        # Likely abbreviation -> try expand first
        result = expand(query)
        if result:
            return result
        return abbreviate(query)
    else:
        # Likely full name -> try abbreviate first
        result = abbreviate(query)
        if result:
            return result
        return expand(query)


# --- BibTeX Processing ---


def process_bib(filepath, direction="abbreviate"):
    """Process a .bib file, replacing journal names."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return None

    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(r"(journal\s*=\s*\{)([^}]+)(\})", re.IGNORECASE)
    changes = []

    def replacer(m):
        prefix, name, suffix = m.group(1), m.group(2).strip(), m.group(3)
        if direction == "abbreviate":
            result = abbreviate(name)
        else:
            result = expand(name)

        if result:
            new_name = result["abbreviation"] if direction == "abbreviate" else result["full"]
            if new_name != name:
                changes.append({"old": name, "new": new_name, "source": result["source"]})
                return f"{prefix}{new_name}{suffix}"
        return m.group(0)

    new_text = pattern.sub(replacer, text)

    # Write output
    out_path = path.with_stem(path.stem + "_abbrev" if direction == "abbreviate" else path.stem + "_full")
    out_path.write_text(new_text, encoding="utf-8")

    return {"input": str(path), "output": str(out_path), "changes": changes}


def batch_lookup(filepath):
    """Process a text file with one journal name per line."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return None

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines:
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        result = auto_lookup(name)
        if result:
            results.append(result)
        else:
            results.append({"query": name, "full": name, "abbreviation": "NOT FOUND", "source": "-"})
    return results


# --- Output Formatting ---


def format_result(result):
    """Format a single result for display."""
    if result is None:
        return "No result found."
    lines = [
        f"  Full name:    {result.get('full', 'N/A')}",
        f"  Abbreviation: {result.get('abbreviation', 'N/A')}",
        f"  Source:       {result.get('source', 'N/A')}",
    ]
    if "standard" in result:
        lines.append(f"  Standard:     {result['standard']}")
    return "\n".join(lines)


def format_table(results):
    """Format results as a table."""
    if not results:
        return "No results."
    # Calculate column widths
    headers = ["Full Name", "Abbreviation", "Source"]
    rows = [(r.get("full", ""), r.get("abbreviation", ""), r.get("source", "")) for r in results]
    widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    hdr = "|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|"
    lines = [sep, hdr, sep]
    for row in rows:
        lines.append("|" + "|".join(f" {row[i]:<{widths[i]}} " for i in range(3)) + "|")
    lines.append(sep)
    return "\n".join(lines)


def format_json(data):
    """Format data as JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False)


# --- CLI ---


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    output_json = "--json" in sys.argv
    args = [a for a in sys.argv[2:] if a != "--json"]

    if cmd == "lookup":
        if not args:
            print("Usage: jabbrv.py lookup <journal name>", file=sys.stderr)
            sys.exit(1)
        query = " ".join(args)
        result = auto_lookup(query)
        if output_json:
            print(format_json(result))
        elif result:
            print(format_result(result))
        else:
            print(f"No result found for: {query}")

    elif cmd == "abbrev":
        if not args:
            print("Usage: jabbrv.py abbrev <full journal name>", file=sys.stderr)
            sys.exit(1)
        query = " ".join(args)
        result = abbreviate(query)
        if output_json:
            print(format_json(result))
        elif result:
            print(format_result(result))
        else:
            print(f"No abbreviation found for: {query}")

    elif cmd == "expand":
        if not args:
            print("Usage: jabbrv.py expand <abbreviation>", file=sys.stderr)
            sys.exit(1)
        query = " ".join(args)
        result = expand(query)
        if output_json:
            print(format_json(result))
        elif result:
            print(format_result(result))
        else:
            print(f"No expansion found for: {query}")

    elif cmd == "search":
        if not args:
            print("Usage: jabbrv.py search <query>", file=sys.stderr)
            sys.exit(1)
        query = " ".join(args)
        results = fuzzy_search(query, n=15)
        if output_json:
            print(format_json(results))
        elif results:
            print(format_table(results))
        else:
            print(f"No matches found for: {query}")

    elif cmd == "bib":
        if not args:
            print("Usage: jabbrv.py bib <file.bib> [--expand]", file=sys.stderr)
            sys.exit(1)
        filepath = args[0]
        direction = "expand" if "--expand" in args else "abbreviate"
        result = process_bib(filepath, direction)
        if result:
            if output_json:
                print(format_json(result))
            else:
                print(f"Input:  {result['input']}")
                print(f"Output: {result['output']}")
                print(f"Changes: {len(result['changes'])}")
                for c in result["changes"]:
                    print(f"  {c['old']}  →  {c['new']}  ({c['source']})")
        else:
            print("Failed to process .bib file.")

    elif cmd == "batch":
        if not args:
            print("Usage: jabbrv.py batch <journals.txt>", file=sys.stderr)
            sys.exit(1)
        results = batch_lookup(args[0])
        if results:
            if output_json:
                print(format_json(results))
            else:
                print(format_table(results))

    elif cmd == "update-cache":
        global _cache
        _cache = None
        # Remove existing cache files to force re-download
        if CACHE_DIR.exists():
            for f in CACHE_DIR.iterdir():
                if f.suffix == ".csv":
                    f.unlink()
        ensure_cache()
        full_to_abbrev, _ = load_cache()
        print(f"Cache updated. {len(full_to_abbrev)} journals loaded.")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
