# Coding Standards

## Python

- Target Python 3.10+ (Pi OS); PEP 8, line length 88 (ruff and black are configured in `pyproject.toml`)
- Type hints and docstrings with Args / Returns, as in `control_panel.py`
- Meaningful names; comments only for non-obvious WHY
- Functions focused and single-purpose
- Prefer the standard library. Existing stack is gspread + oauth2client; do not introduce new Sheets clients alongside them
- Script return values follow [SCRIPT_CONTRACT.md](SCRIPT_CONTRACT.md)

## Logging and output

- Library code uses `logging` (see `ControlPanel._setup_logger`, format `[%(asctime)s] %(levelname)s: %(message)s`)
- Existing scripts print emoji status lines to the console. Match the surrounding file when editing it, but do not add emojis to new documentation, commit messages, comments, or identifiers
- No stray debug prints or commented-out code left in scripts
- Never log credential contents, key IDs, or the Pi IP

## Errors

- Validate at the boundaries: sheet parameters (always strings, may be missing or blank) and anything from the network
- Do not add defensive checks for internal states that cannot occur
- Expected failures return `(False, message, details)`; do not let them raise

## Shell scripts

- Bash, `set -e` in setup scripts, Linux (LF) line endings
- Keep the existing colour-coded echo style and "confirm before proceeding" prompts
- Quote variables; do not add `rm -rf` or destructive operations without a prompt

## Dependencies

- Add to `pyproject.toml` only when required; mention it to the user because the Pi must `uv sync`
- Do not bump `requires-python` or remove unused deps (pandas, numpy, matplotlib) unasked
