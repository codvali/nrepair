# nrepair — project rules

## Golden rule (never violate)

The owner/author of this project is **Condei Valentin** (VOENSYS.COM / VAOS).

- NEVER add "Generated with Devin" or "Co-Authored-By" trailers to commits.
- NEVER include tool/agent attribution in commit messages or files.
- Commit messages are plain; authorship is always Condei Valentin
  `<valentincondei@yahoo.com>` (set via repo-local git config).

## Stack

- Python 3 + stdlib only (tkinter, subprocess, json, dataclasses)
- Tkinter GUI + CLI, bilingual ro/en (i18n via `nrepair/i18n/strings.py`)
- Read-only collectors via PowerShell/WMI; parallel via ThreadPoolExecutor
- Build: `pyinstaller nrepair.spec` → `dist/nrepair.exe`

## Verify

```powershell
python main.py --cli --lang en   # run scan in terminal
python main.py                    # launch GUI
pyinstaller nrepair.spec          # build .exe
```
