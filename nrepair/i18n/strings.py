# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Bilingual string table (Romanian / English) with English fallback.

Usage:
    from nrepair.i18n.strings import t
    t("summary_title", "ro")   -> "Rezumat"
    t("summary_title", "en")   -> "Summary"
"""

SUPPORTED = ("ro", "en")
DEFAULT = "en"

# key -> {"ro": ..., "en": ...}
_STRINGS = {
    # ---- app / generic ----
    "app_title": {
        "ro": "nrepair — Diagnostic PC",
        "en": "nrepair — PC Diagnostic",
    },
    "app_subtitle": {
        "ro": "Doar citire | Fără modificări | Explicații omenești",
        "en": "Read-only | No modifications | Human-friendly explanations",
    },
    "lang_label": {
        "ro": "Limbă:",
        "en": "Language:",
    },
    "btn_scan": {
        "ro": "[1] Scanează PC",
        "en": "[1] Scan PC",
    },
    "btn_export_html": {
        "ro": "Export HTML",
        "en": "Export HTML",
    },
    "btn_export_json": {
        "ro": "Export JSON",
        "en": "Export JSON",
    },
    "btn_export_md": {
        "ro": "Export Markdown",
        "en": "Export Markdown",
    },
    "btn_show_details": {
        "ro": "[ Afișează detalii ]",
        "en": "[ Show details ]",
    },
    "btn_copy": {
        "ro": "Copiază rezumat",
        "en": "Copy summary",
    },
    "btn_about": {
        "ro": "Despre / Donează",
        "en": "About / Donate",
    },

    # ---- about / donate window ----
    "about_title": {
        "ro": "Despre — nrepair",
        "en": "About — nrepair",
    },
    "about_tagline": {
        "ro": "Diagnostic PC pentru utilizatorul normal",
        "en": "PC diagnostic for the normal user",
    },
    "about_readonly_badge": {
        "ro": "DOAR CITIRE | Stdlib Python | Fără modificări",
        "en": "READ-ONLY | Python stdlib | No modifications",
    },
    "about_author_h": {"ro": "PROPRIETAR / AUTOR", "en": "OWNER / AUTHOR"},
    "about_author_name": {"ro": "Condei Valentin", "en": "Condei Valentin"},
    "about_email": {"ro": "valentincondei@yahoo.com", "en": "valentincondei@yahoo.com"},
    "about_company": {"ro": "VOENSYS.COM / VAOS", "en": "VOENSYS.COM / VAOS"},
    "about_links_h": {"ro": "PAGINI", "en": "PAGES"},
    "about_link_en": {"ro": "Pagina EN", "en": "EN Page"},
    "about_link_ro": {"ro": "Pagina RO", "en": "RO Page"},
    "about_more_utils": {"ro": "Mai multe utilitare: EN | RO", "en": "More utilities: EN | RO"},
    "about_libs_h": {"ro": "BIBLIOTECI FOLOSITE", "en": "LIBRARIES USED"},
    "about_libs_body": {
        "ro": "Python 3 + tkinter (PSF License)\n\nFără dependențe externe la runtime.\nDoar biblioteca standard Python.",
        "en": "Python 3 + tkinter (PSF License)\n\nNo external runtime dependencies.\nPython standard library only.",
    },
    "about_donate_h": {"ro": "SUSȚINE PROIECTUL", "en": "SUPPORT THIS PROJECT"},
    "about_donate_msg": {
        "ro": "Dacă acest utilitar te-a ajutat, consideră o donație:",
        "en": "If this tool helped you, consider a donation:",
    },
    "about_close": {"ro": "Închide", "en": "Close"},
    "status_idle": {
        "ro": "Inactiv. Apasă „Scanează PC” pentru a începe.",
        "en": "Idle. Press \"Scan PC\" to start.",
    },
    "status_scanning": {
        "ro": "Scanez {cat}…",
        "en": "Scanning {cat}…",
    },
    "status_done": {
        "ro": "Gata. {n} probleme găsite.",
        "en": "Done. {n} problems found.",
    },
    "status_done_clean": {
        "ro": "Gata. Nicio problemă semnificativă. PC-ul arată bine.",
        "en": "Done. No significant problems. PC looks healthy.",
    },
    "export_saved": {
        "ro": "Raport salvat: {path}",
        "en": "Report saved: {path}",
    },
    "export_failed": {
        "ro": "Export eșuat: {err}",
        "en": "Export failed: {err}",
    },
    "copied": {
        "ro": "Rezumat copiat în clipboard.",
        "en": "Summary copied to clipboard.",
    },

    # ---- severity ----
    "sev_critical": {"ro": "CRITIC", "en": "CRITICAL"},
    "sev_warning": {"ro": "AVERTISMENT", "en": "WARNING"},
    "sev_info": {"ro": "INFO", "en": "INFO"},

    # ---- summary tab ----
    "summary_tab": {"ro": "Rezumat", "en": "Summary"},
    "summary_problem_found": {"ro": "PROBLEMĂ GĂSITĂ", "en": "PROBLEM FOUND"},
    "summary_no_problems": {
        "ro": "Nicio problemă semnificativă detectată.",
        "en": "No significant problems detected.",
    },
    "summary_recommendation": {"ro": "RECOMANDARE:", "en": "RECOMMENDATION:"},
    "summary_no_recommendation": {
        "ro": "Nu sunt recomandări urgente.",
        "en": "No urgent recommendations.",
    },
    "summary_steps": {"ro": "Pași:", "en": "Steps:"},

    # ---- category names ----
    "cat_disk": {"ro": "Disc", "en": "Disk"},
    "cat_space": {"ro": "Spațiu liber", "en": "Free space"},
    "cat_ram": {"ro": "RAM", "en": "RAM"},
    "cat_cpu": {"ro": "CPU", "en": "CPU"},
    "cat_temps": {"ro": "Temperaturi", "en": "Temperatures"},
    "cat_services": {"ro": "Servicii", "en": "Services"},
    "cat_startup": {"ro": "Pornire", "en": "Startup"},
    "cat_drivers": {"ro": "Drivere", "en": "Drivers"},
    "cat_network": {"ro": "Rețea", "en": "Network"},
    "cat_sysfiles": {"ro": "Fișiere sistem", "en": "System files"},
    "cat_events": {"ro": "Erori recente", "en": "Recent errors"},

    # ---- generic collector labels ----
    "label_status": {"ro": "Stare", "en": "Status"},
    "label_ok": {"ro": "OK", "en": "OK"},
    "label_unknown": {"ro": "Necunoscut", "en": "Unknown"},
    "label_na": {"ro": "N/A", "en": "N/A"},
    "label_total": {"ro": "Total", "en": "Total"},
    "label_free": {"ro": "Liber", "en": "Free"},
    "label_used": {"ro": "Folosit", "en": "Used"},
    "label_name": {"ro": "Nume", "en": "Name"},
    "label_count": {"ro": "Număr", "en": "Count"},
    "label_details": {"ro": "Detalii", "en": "Details"},
    "label_none_found": {"ro": "Nimic relevant.", "en": "Nothing relevant."},

    # ---- disk ----
    "disk_health": {"ro": "Stare disc", "en": "Disk health"},
    "disk_smart_ok": {
        "ro": "SMART raportează discul sănătos.",
        "en": "SMART reports the disk as healthy.",
    },
    "disk_smart_warning": {
        "ro": "SMART a raportat avertismente pentru {disk}.",
        "en": "SMART reported warnings for {disk}.",
    },
    "disk_smart_critical": {
        "ro": "SMART a raportat probleme critice pentru {disk}. Fă backup imediat!",
        "en": "SMART reported critical issues for {disk}. Back up immediately!",
    },
    "disk_smart_unavailable": {
        "ro": "Datele SMART nu sunt accesibile pentru {disk}.",
        "en": "SMART data is not accessible for {disk}.",
    },
    "disk_rec_backup": {
        "ro": "Fă backup imediat la datele importante și înlocuiește discul cât mai curând.",
        "en": "Back up important data immediately and replace the disk ASAP.",
    },
    "disk_rec_check": {
        "ro": "Rulează: chkdsk /f  (din CMD ca Administrator) și monitorizează discul.",
        "en": "Run: chkdsk /f  (from CMD as Administrator) and monitor the disk.",
    },

    # ---- space ----
    "space_low": {
        "ro": "Spațiu liber pe {drive}: {pct}% (sub pragul de {threshold}%).",
        "en": "Free space on {drive}: {pct}% (below {threshold}% threshold).",
    },
    "space_ok": {
        "ro": "Spațiu liber pe {drive}: {pct}%.",
        "en": "Free space on {drive}: {pct}%.",
    },
    "space_rec_free": {
        "ro": "Eliberează cel puțin {gb} GB pe {drive} (șterge fișiere temporare, descărcări vechi, golire coș).",
        "en": "Free at least {gb} GB on {drive} (delete temp files, old downloads, empty recycle bin).",
    },
    "space_rec_update_cache": {
        "ro": "Cache Windows Update: {gb} GB. Poate fi curățat din „Setări → Sistem → Stocare → Fișiere temporare”.",
        "en": "Windows Update cache: {gb} GB. Can be cleaned via \"Settings → System → Storage → Temporary files\".",
    },

    # ---- RAM ----
    "ram_total": {"ro": "RAM totală", "en": "Total RAM"},
    "ram_free": {"ro": "RAM liberă", "en": "Free RAM"},
    "ram_low": {
        "ro": "RAM liberă foarte scăzută ({pct}%). Aplicațiile pot fi lente.",
        "en": "Free RAM is very low ({pct}%). Apps may be slow.",
    },
    "ram_rec_close": {
        "ro": "Închide aplicații grele sau adaugă RAM fizică.",
        "en": "Close heavy apps or add physical RAM.",
    },
    "ram_free": {
        "ro": "RAM liberă: {pct}%.",
        "en": "Free RAM: {pct}%.",
    },

    # ---- CPU ----
    "cpu_load_high": {
        "ro": "Încărcare CPU mare ({pct}%) timp îndelungat.",
        "en": "High CPU load ({pct}%) for a sustained period.",
    },
    "cpu_rec_investigate": {
        "ro": "Deschide Task Manager → Detalii și sortează după CPU pentru a găsi procesul.",
        "en": "Open Task Manager → Details and sort by CPU to find the process.",
    },
    "cpu_load_ok": {
        "ro": "Încărcare CPU: {pct}%.",
        "en": "CPU load: {pct}%.",
    },

    # ---- temps ----
    "temps_unavailable": {
        "ro": "Temperaturile nu sunt accesibile (WMI nu expune senzori pe acest sistem).",
        "en": "Temperatures not accessible (WMI does not expose sensors on this system).",
    },
    "temps_high": {
        "ro": "Temperatură ridicată: {zone} = {temp}°C.",
        "en": "High temperature: {zone} = {temp}°C.",
    },
    "temps_rec_dust": {
        "ro": "Curăță praful din cooler / verifică ventilația.",
        "en": "Clean dust from cooler / check ventilation.",
    },
    "temps_ok": {
        "ro": "Temperatură normală: {zone} = {temp}°C.",
        "en": "Normal temperature: {zone} = {temp}°C.",
    },

    # ---- services ----
    "services_failed": {
        "ro": "{n} servicii au eșuat recent.",
        "en": "{n} services failed recently.",
    },
    "services_rec_restart": {
        "ro": "Deschide services.msc, găsește serviciile care au eșuat (vezi lista în tab-ul „Servicii”) și repornește-le.",
        "en": "Open services.msc, find the services that failed (see list in the \"Services\" tab) and restart them.",
    },
    "services_rec_restart_one": {
        "ro": "Repornește serviciul „{name}” din services.msc sau cu: sc start \"{name}\".",
        "en": "Restart service \"{name}\" from services.msc or with: sc start \"{name}\".",
    },
    "services_stopped_auto": {
        "ro": "Serviciu automat oprit: {name}.",
        "en": "Automatic service stopped: {name}.",
    },

    # ---- startup ----
    "startup_many": {
        "ro": "{n} programe pornesc automat. Poate încetini pornirea PC.",
        "en": "{n} programs start automatically. May slow down PC boot.",
    },
    "startup_rec_disable": {
        "ro": "Dezactivează din Task Manager → Pornire ce nu folosești zilnic.",
        "en": "Disable in Task Manager → Startup what you don't use daily.",
    },
    "startup_ok": {
        "ro": "{n} programe la pornire — în limite normale.",
        "en": "{n} startup programs — within normal range.",
    },

    # ---- drivers ----
    "drivers_problem": {
        "ro": "{n} drivere cu probleme (semnate lipsă sau cu eroare).",
        "en": "{n} drivers with problems (missing signature or error).",
    },
    "drivers_rec_update": {
        "ro": "Actualizează driverele din Device Manager sau site-ul producătorului.",
        "en": "Update drivers via Device Manager or the manufacturer's website.",
    },
    "drivers_ok": {
        "ro": "Toate driverele semnate au status OK.",
        "en": "All signed drivers report OK status.",
    },

    # ---- network ----
    "net_adapter_down": {
        "ro": "Adaptor de rețea dezactivat: {name}.",
        "en": "Network adapter disabled: {name}.",
    },
    "net_no_default_gateway": {
        "ro": "Niciun gateway implicit — posibil fără internet.",
        "en": "No default gateway — possibly no internet.",
    },
    "net_rec_enable": {
        "ro": "Activează adaptorul din Setări → Rețea sau cu: netsh interface set interface \"{name}\" admin=enable.",
        "en": "Enable the adapter from Settings → Network or with: netsh interface set interface \"{name}\" admin=enable.",
    },

    # ---- system files ----
    "sysfiles_not_scanned": {
        "ro": "Verificarea fișierelor de sistem (sfc/dism) nu a fost rulată — necesită admin și durează minute.",
        "en": "System file check (sfc/dism) was not run — requires admin and takes minutes.",
    },
    "sysfiles_rec_run": {
        "ro": "Deschide CMD ca Administrator și rulează: sfc /scannow  (apoi dism /online /Cleanup-Image /RestoreHealth dacă sfc găsește erori).",
        "en": "Open CMD as Administrator and run: sfc /scannow  (then dism /online /Cleanup-Image /RestoreHealth if sfc finds errors).",
    },
    "sysfiles_last_sfc_ok": {
        "ro": "Ultima verificare sfc: {status}.",
        "en": "Last sfc check: {status}.",
    },

    # ---- events ----
    "events_critical": {
        "ro": "{n} erori critice în ultimele 48h.",
        "en": "{n} critical errors in the last 48h.",
    },
    "events_rec_review": {
        "ro": "Deschide Event Viewer → Windows Logs → System/Application și filtrează după „Critical/Error”.",
        "en": "Open Event Viewer → Windows Logs → System/Application and filter by \"Critical/Error\".",
    },
    "events_ok": {
        "ro": "Nicio eroare critică în ultimele 48h.",
        "en": "No critical errors in the last 48h.",
    },
    "events_source": {"ro": "Sursă", "en": "Source"},
    "events_time": {"ro": "Timp", "en": "Time"},
    "events_message": {"ro": "Mesaj", "en": "Message"},

    # ---- report ----
    "report_title": {"ro": "Raport nrepair", "en": "nrepair Report"},
    "report_generated": {"ro": "Generat la", "en": "Generated at"},
    "report_machine": {"ro": "Mașină", "en": "Machine"},
    "report_problems": {"ro": "Probleme", "en": "Problems"},
    "report_categories": {"ro": "Categorii", "en": "Categories"},
    "report_no_data": {"ro": "Rulește un scan pentru a genera raportul.", "en": "Run a scan to generate the report."},
}


def t(key: str, lang: str = DEFAULT, **fmt) -> str:
    """Translate a key. Falls back to English, then to the key itself."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT) or key
    if fmt:
        try:
            text = text.format(**fmt)
        except Exception:
            pass
    return text


def available_keys():
    return sorted(_STRINGS.keys())
