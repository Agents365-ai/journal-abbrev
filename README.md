# Journal Abbrev — Journal Name Abbreviation Lookup Skill

[中文](README_CN.md)

A Claude Code skill for looking up standard journal/magazine name abbreviations. Supports both ISO 4 and MEDLINE abbreviation standards, covering 25,000+ journals.

## Features

| Feature | Native Claude Code | Journal Abbrev |
|---------|-------------------|----------------|
| Journal abbreviation lookup | Manual guessing | Multi-source cascade, accurate results |
| Reverse lookup (abbrev → full) | Not supported | Bidirectional lookup |
| BibTeX batch processing | Not supported | Auto-replace journal fields |
| Fuzzy search | Not supported | Partial name matching |
| Offline lookup | Not supported | Local cache with 25K+ journals |

## Data Sources

1. **JabRef Database** — 25,000+ journals, CC0 licensed, auto-downloaded on first run
2. **AbbrevISO API** — Algorithmic ISO 4 abbreviation based on LTWA (forward only)
3. **NLM Catalog** — Bidirectional lookup for biomedical journals (MEDLINE standard)

## Installation

### Claude Code

```bash
# Global install
git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.claude/skills/journal-abbrev

# Project-level install
git clone https://github.com/Agents365-ai/journal-abbrev.git .claude/skills/journal-abbrev
```

### OpenClaw

```bash
git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.openclaw/skills/journal-abbrev
```

### SkillsMP

Search for `journal-abbrev` on [skillsmp.com](https://skillsmp.com) and install.

## Usage

### Natural Language

Ask Claude directly:

- "What's the abbreviation for Nature Medicine?"
- "What journal is J. Biol. Chem.?"
- "Abbreviate all journal names in refs.bib"
- "Search for journals related to biolog chem"

### Command Line

```bash
# Auto-detect direction
python3 jabbrv.py lookup "Nature Medicine"

# Full name → abbreviation
python3 jabbrv.py abbrev "Journal of Biological Chemistry"

# Abbreviation → full name
python3 jabbrv.py expand "Nat. Med."

# Fuzzy search
python3 jabbrv.py search "biolog chem"

# Process BibTeX file
python3 jabbrv.py bib refs.bib

# Batch lookup (one journal per line)
python3 jabbrv.py batch journals.txt

# Update local cache
python3 jabbrv.py update-cache
```

All commands support `--json` flag for JSON output.

## Requirements

- Python 3.6+ (no third-party packages required)

## License

MIT
