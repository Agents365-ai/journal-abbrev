# Journal Abbreviation Tool — Agent Context

This repository provides **`jabbrv`**, a journal name abbreviation CLI with a
JabRef → AbbrevISO → NLM cascade covering 25,000+ journals. It is designed to
serve AI agents and humans simultaneously through a stable JSON contract.

If you are an AI agent reading this file, everything you need to know to use
this tool correctly is in the four sections below.

## 1. What to invoke

The tool is a single Python file at `./jabbrv.py`. It has no dependencies
beyond the Python 3.9+ standard library. Run it via:

```bash
python3 jabbrv.py <subcommand> [args...]
```

When stdout is not a TTY (which is the case whenever an agent captures output),
every subcommand returns a stable JSON envelope on stdout. You do **not** need
`--json` — format is auto-detected. Prose, warnings, and progress all go to
stderr.

## 2. The output envelope

Every response has exactly one of three shapes:

| Shape | When | Example |
|---|---|---|
| Success | the command completed and has a result | `{"ok": true, "data": {...}, "meta": {...}}` |
| Partial success | batch operation where some items succeeded and some failed | `{"ok": "partial", "data": {"succeeded": [...], "failed": [...]}, "meta": {...}}` |
| Error | the command could not complete | `{"ok": false, "error": {"code": "...", "message": "...", "retryable": bool}, "meta": {...}}` |

**Exit codes** map to failure class so you can route on them without parsing:

| Code | Meaning |
|---|---|
| `0` | success (including partial success) |
| `1` | runtime / upstream error |
| `2` | validation / bad input (missing file, invalid flag) |
| `3` | not found |

**Error codes** inside `error.code`: `not_found`, `file_not_found`,
`validation_error`, `runtime_error`. Each carries `retryable: bool` — respect
it. `retryable: false` means retrying will not help; escalate or fix the input.

**`meta.cache`** on any lookup response tells you the health of the local
JabRef cache. If `meta.cache.files_failed` is non-empty, some CSVs failed to
download and a negative lookup ("not found") may be wrong. Re-run
`python3 jabbrv.py cache update` and try again before trusting the result.

## 3. Common invocations

```bash
# Single lookups
python3 jabbrv.py lookup "Nature Medicine"              # auto-detect direction
python3 jabbrv.py abbrev "Journal of Biological Chemistry"
python3 jabbrv.py expand "Nat. Med."

# Fuzzy search (paginated — always check page.has_more)
python3 jabbrv.py search "biol chem" --limit 10 --offset 0

# BibTeX processing (ALWAYS dry-run first to preview)
python3 jabbrv.py bib refs.bib --dry-run
python3 jabbrv.py bib refs.bib --output refs_final.bib

# Batch processing
python3 jabbrv.py batch journals.txt                    # single envelope at end
python3 jabbrv.py batch journals.txt --stream           # NDJSON per line

# Cache management
python3 jabbrv.py cache status                          # inspect local state
python3 jabbrv.py cache update                          # download missing files
python3 jabbrv.py cache rebuild                         # delete + redownload all
```

## 4. Discovering the full contract

Never guess a flag name. The CLI is self-describing:

```bash
python3 jabbrv.py --help                 # top-level help
python3 jabbrv.py <command> --help       # per-command help
python3 jabbrv.py schema                 # full machine-readable schema
python3 jabbrv.py schema <command>       # schema for one command
```

`schema` is the authoritative source of truth for subcommands, params, types,
defaults, choices, exit codes, and the envelope shape. It is versioned via
`meta.schema_version`. Prefer it over any cached knowledge you may have.

## When to use this tool

Route any user request to `jabbrv` when it involves:

- A journal name abbreviation in either direction (full ↔ abbreviated)
- Standardizing journal names in a BibTeX file before manuscript submission
- ISO 4, MEDLINE, LTWA, or "期刊缩写 / 杂志缩写"
- Reference list preparation for a specific journal's citation style

**Do not guess abbreviations.** Even common journals have non-obvious
abbreviations (e.g., *Nature* does not abbreviate; *Journal of the American
Chemical Society* becomes *J. Am. Chem. Soc.*, not *JACS*). Always route
through `jabbrv`.

## Agent-platform notes

This file follows the `AGENTS.md` convention. It is auto-discovered by OpenAI
Codex CLI, Claude Code (as a fallback to `CLAUDE.md`), Gemini CLI, Cursor
(recent versions), Aider, and other agent runtimes that scan the repository
root. For platforms that use their own rule-file conventions (GitHub Copilot
Chat, Continue.dev, Windsurf), see the **Installation** section of `README.md`
for one-line snippets that point those files at this one.

For Claude Code, OpenClaw, ClawHub, and SkillsMP, the canonical skill manifest
lives in `SKILL.md`. This file and that one describe the same tool.
