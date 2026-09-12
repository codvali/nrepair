# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ║                         All Rights Reserved                  ║
# ╚══════════════════════════════════════════════════════════════╝

# nrepair — „Ce este în neregulă cu PC-ul meu?"

**RO** | [EN](#en)

Un diagnostic PC pentru **utilizatorul normal**. Nu se termină cu `ERROR`,
ci îți spune ce nu e în regulă, **de ce contează** și **ce să faci** — pas cu pas.

Windows are deja multe instrumente individuale (`sfc`, `dism`, `chkdsk`,
Event Viewer, Device Manager…), dar sunt împrăștiate și nu explică bine
ce înseamnă rezultatul. `nrepair` le adună într-un singur loc și le traduce
în limbaj omenezesc.

```
PROBLEMĂ GĂSITĂ

[AVERTISMENT] Spațiu liber
  Spațiu liber pe C:: 7% (sub pragul de 10%).
  RECOMANDARE:
   1. Eliberează cel puțin 13 GB pe C: (șterge fișiere temporare, descărcări vechi, golire coș).
   2. Cache Windows Update: 18.4 GB. Poate fi curățat din „Setări → Sistem → Stocare → Fișiere temporare".

[ Afișează detalii ] → Spațiu liber
```

## Ce verifică

| Categorie | Sursă de date |
|---|---|
| Disc (SMART) | `Get-PhysicalDisk` |
| Spațiu liber | `Get-Volume` + dimensiune cache Windows Update |
| RAM | `Win32_OperatingSystem` |
| CPU | `Win32_Processor` |
| Temperaturi | `MSAcpi_ThermalZoneTemperature` (unde e accesibil) |
| Servicii | `Win32_Service` + Event Log (eșuări recente) |
| Pornire | `Win32_StartupCommand` |
| Drivere | `Win32_PnPSignedDriver` (status Error/Degraded) |
| Rețea | `Get-NetAdapter` + gateway implicit |
| Fișiere sistem | hint din `CBS.log` + recomandare `sfc /scannow` |
| Erori recente | Event Log System/Application (ultimele 48h) |

## Principii

- **Read-only**: nu modifică sistemul. Nu rulează `sfc`, `dism`, `chkdsk`,
  nu oprește/repornește servicii, nu șterge fișiere. Doar citește și explică.
- **Fără admin necesar** pentru majoritatea verificărilor (sfc/dism sunt
  recomandate să le rulezi manual, cu admin).
- **i18n**: română + engleză, switch live în GUI.
- **Doar stdlib**: fără dependențe externe la runtime.

## Rulare

### Din sursă (Python 3.9+)

```powershell
python main.py                 # GUI
python main.py --cli           # terminal
python main.py --cli --lang en --export-md report.md
```

### Executabil standalone

Descarcă `nrepair.exe` din [Releases](../../releases) și rulează dublu-click.
Nu necesită instalare, nu necesită Python.

## Build .exe

```powershell
pip install -r requirements.txt
pyinstaller nrepair.spec
# rezultat: dist\nrepair.exe
```

## Export raport

Din GUI: butoanele **Export HTML / JSON / Markdown**.
Rapoartele se salvează în `C:\Users\<tu>\nrepair_reports\`.

## Structură proiect

```
nrepair/
├── nrepair/
│   ├── core/
│   │   ├── model.py        # Finding / Problem / Recommendation
│   │   ├── collectors.py   # 11 colectoare read-only (PowerShell/WMI)
│   │   ├── rules.py        # reguli → probleme prioritizate
│   │   └── report.py       # export HTML / JSON / Markdown
│   ├── i18n/strings.py     # tabel de stringuri ro/en
│   └── gui/app.py          # interfață Tkinter
├── main.py                 # entry point (GUI + CLI)
├── nrepair.spec            # PyInstaller
├── requirements.txt
├── LICENSE
└── README.md
```

## Limitări cunoscute

- Temperaturile sunt accesibile doar dacă WMI expune `MSAcpi_ThermalZoneTemperature`
  (pe multe laptopuri/consumere nu e expus — se afișează „N/A").
- Verificarea fișierelor de sistem (`sfc`/`dism`) nu este rulată automat
  (necesită admin + minute bune) — se oferă doar recomandarea.
- Event Log-ul poate fi lent pe sisteme cu multe evenimente (timeout 90s).

## Licență

Proprietary — All Rights Reserved © 2026 Valentin Condei.
Vezi [LICENSE](LICENSE). Utilizarea executabilului e gratuită (personal/comercial).

---

<a name="en"></a>
# nrepair — „What's wrong with my PC?" (EN)

A PC diagnostic for the **normal user**. It doesn't end with `ERROR` —
it tells you what's wrong, **why it matters**, and **what to do**, step by step.

Windows already has many individual tools (`sfc`, `dism`, `chkdsk`, Event
Viewer, Device Manager…), but they're scattered and don't explain what the
result means. `nrepair` gathers them in one place and translates them into
plain language.

## What it checks

Disk (SMART), free space (+ Windows Update cache size), RAM, CPU,
temperatures (where exposed), services (+ recent failures), startup
programs, drivers (Error/Degraded only), network (adapter + default
gateway), system files (CBS.log hint + `sfc` recommendation), recent
errors (System/Application logs, last 48h).

## Principles

- **Read-only**: never mutates the system. No `sfc`/`dism`/`chkdsk` run,
  no services stopped/started, no files deleted. It only reads and explains.
- **No admin required** for most checks (sfc/dism are recommended to run
  manually, with admin).
- **i18n**: Romanian + English, live switch in the GUI.
- **Stdlib only**: no external runtime dependencies.

## Run

```powershell
python main.py                 # GUI
python main.py --cli           # terminal
python main.py --cli --lang en --export-md report.md
```

Or download `nrepair.exe` from [Releases](../../releases) — no install, no Python needed.

## Build .exe

```powershell
pip install -r requirements.txt
pyinstaller nrepair.spec
```

## License

Proprietary — All Rights Reserved © 2026 Valentin Condei. See [LICENSE](LICENSE).
Free to use the executable (personal/commercial).
