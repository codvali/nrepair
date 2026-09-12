# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Read-only data collectors for nrepair.

Each collector returns a CategoryResult. None of them mutate the system.
They shell out to PowerShell (built into Windows) for WMI / cmdlets and
parse JSON via ConvertTo-Json so we avoid fragile text scraping.

Every collector is wrapped so a crash is recorded in CategoryResult.error
instead of taking down the whole scan.
"""

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from .model import CategoryResult, Finding, OK, INFO, WARNING, CRITICAL

# category keys (must match i18n keys "cat_*")
CAT_DISK = "cat_disk"
CAT_SPACE = "cat_space"
CAT_RAM = "cat_ram"
CAT_CPU = "cat_cpu"
CAT_TEMPS = "cat_temps"
CAT_SERVICES = "cat_services"
CAT_STARTUP = "cat_startup"
CAT_DRIVERS = "cat_drivers"
CAT_NETWORK = "cat_network"
CAT_SYSFILES = "cat_sysfiles"
CAT_EVENTS = "cat_events"

ALL_CATEGORIES = [
    CAT_DISK, CAT_SPACE, CAT_RAM, CAT_CPU, CAT_TEMPS,
    CAT_SERVICES, CAT_STARTUP, CAT_DRIVERS, CAT_NETWORK,
    CAT_SYSFILES, CAT_EVENTS,
]


# ---------------------------------------------------------------------------
# PowerShell helper
# ---------------------------------------------------------------------------
def _ps(script: str, timeout: int = 60) -> Any:
    """Run a PowerShell snippet that ends with ConvertTo-Json -Depth 6 -Compress
    and return the parsed Python object. Raises on failure."""
    full = (
        "$ErrorActionPreference='SilentlyContinue';"
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        + script
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", full],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8",
        errors="replace",
        # Hide the PowerShell console window so the GUI scan does not flash
        # 11 black cmd windows on screen. CREATE_NO_WINDOW = 0x08000000.
        creationflags=0x08000000,
    )
    text = (out.stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # PowerShell may emit multiple JSON objects; take the last valid line block
        # fallback: return raw text
        return text


def _safe(key: str, fn) -> CategoryResult:
    """Wrap a collector so exceptions become CategoryResult.error."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        return CategoryResult(key=key, error=f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------
def collect_disk() -> CategoryResult:
    """Physical disks + SMART health via WMI."""
    res = CategoryResult(key=CAT_DISK)
    data = _ps(
        "Get-PhysicalDisk | Select-Object DeviceId,FriendlyName,MediaType,"
        "HealthStatus,OperationalStatus,Size | ConvertTo-Json -Depth 6 -Compress;"
    )
    disks = data if isinstance(data, list) else ([data] if data else [])
    res.raw = disks or []
    for d in disks or []:
        name = d.get("FriendlyName") or d.get("DeviceId") or "?"
        health = str(d.get("HealthStatus", "")).lower()
        if health == "healthy":
            res.findings.append(Finding(OK, "disk_smart_ok", {"disk": name}))
        elif health in ("warning", "degraded"):
            res.findings.append(Finding(WARNING, "disk_smart_warning", {"disk": name}))
        elif health in ("unhealthy", "failed"):
            res.findings.append(Finding(CRITICAL, "disk_smart_critical", {"disk": name}))
        else:
            res.findings.append(Finding(INFO, "disk_smart_unavailable", {"disk": name}))
    res.meta = {"disk_count": len(disks or [])}
    return res


def collect_space() -> CategoryResult:
    """Free space per mounted volume + Windows Update cache size."""
    res = CategoryResult(key=CAT_SPACE)
    vols = _ps(
        "Get-Volume | Where-Object {$_.DriveLetter -and $_.Size -gt 0} | "
        "Select-Object DriveLetter,FileSystemLabel,Size,SizeRemaining | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    vols = vols if isinstance(vols, list) else ([vols] if vols else [])
    rows = []
    update_cache_gb = 0.0
    for v in vols or []:
        size = float(v.get("Size") or 0)
        free = float(v.get("SizeRemaining") or 0)
        if size <= 0:
            continue
        pct = round(100 * free / size, 1)
        drive = (v.get("DriveLetter") or "?")
        label = v.get("FileSystemLabel") or ""
        rows.append({"drive": f"{drive}:", "label": label, "total_gb": round(size / 1e9, 1),
                     "free_gb": round(free / 1e9, 1), "free_pct": pct})
        if pct < 10:
            res.findings.append(Finding(CRITICAL, "space_low",
                                        {"drive": f"{drive}:", "pct": pct, "threshold": 10}))
        elif pct < 20:
            res.findings.append(Finding(WARNING, "space_low",
                                        {"drive": f"{drive}:", "pct": pct, "threshold": 20}))
        else:
            res.findings.append(Finding(OK, "space_ok", {"drive": f"{drive}:", "pct": pct}))
        # Windows Update cache lives on C:
        if str(drive).upper().replace(":", "") == "C":
            softdist = r"C:\Windows\SoftwareDistribution\Download"
            try:
                total = 0
                for root, _, files in os.walk(softdist):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except OSError:
                            pass
                update_cache_gb = round(total / 1e9, 1)
            except OSError:
                update_cache_gb = 0.0
    res.raw = rows
    res.meta = {"volumes": rows, "update_cache_gb": update_cache_gb}
    if update_cache_gb >= 1.0:
        res.findings.append(Finding(INFO, "space_rec_update_cache",
                                    {"gb": update_cache_gb}))
    return res


def collect_ram() -> CategoryResult:
    """Total / free RAM."""
    res = CategoryResult(key=CAT_RAM)
    info = _ps(
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "$total=$os.TotalVisibleMemorySize; $free=$os.FreePhysicalMemory;"
        "[pscustomobject]@{TotalKB=[int64]$total; FreeKB=[int64]$free} | "
        "ConvertTo-Json -Compress;"
    )
    info = info if isinstance(info, dict) else {}
    total_kb = int(info.get("TotalKB") or 0)
    free_kb = int(info.get("FreeKB") or 0)
    res.raw = [{"total_gb": round(total_kb / 1e6, 2), "free_gb": round(free_kb / 1e6, 2)}]
    if total_kb > 0:
        free_pct = round(100 * free_kb / total_kb, 1)
        res.meta = {"total_gb": round(total_kb / 1e6, 2), "free_pct": free_pct}
        if free_pct < 10:
            res.findings.append(Finding(CRITICAL, "ram_low", {"pct": free_pct}))
        elif free_pct < 20:
            res.findings.append(Finding(WARNING, "ram_low", {"pct": free_pct}))
        else:
            res.findings.append(Finding(OK, "ram_free", {"pct": free_pct}))
    return res


def collect_cpu() -> CategoryResult:
    """CPU info + current load percentage (snapshot)."""
    res = CategoryResult(key=CAT_CPU)
    cpu = _ps(
        "Get-CimInstance Win32_Processor | Select-Object Name,LoadPercentage,"
        "NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Depth 4 -Compress;"
    )
    cpu = cpu if isinstance(cpu, list) else ([cpu] if cpu else [])
    rows = []
    for c in cpu or []:
        load = c.get("LoadPercentage")
        rows.append({
            "name": c.get("Name", "?"),
            "load_pct": load,
            "cores": c.get("NumberOfCores"),
            "logical": c.get("NumberOfLogicalProcessors"),
        })
        if load is not None and int(load) >= 90:
            res.findings.append(Finding(WARNING, "cpu_load_high", {"pct": load}))
        else:
            res.findings.append(Finding(OK, "cpu_load_ok", {"pct": load}))
    res.raw = rows
    res.meta = {"cpu_count": len(rows)}
    return res


def collect_temps() -> CategoryResult:
    """Thermal zone temperatures where WMI exposes them."""
    res = CategoryResult(key=CAT_TEMPS)
    zones = _ps(
        "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | "
        "Select-Object InstanceName,CurrentTemperature | ConvertTo-Json -Depth 4 -Compress;"
    )
    zones = zones if isinstance(zones, list) else ([zones] if zones else [])
    rows = []
    for z in zones or []:
        raw_temp = z.get("CurrentTemperature")
        if raw_temp is None:
            continue
        # ACPI temps are in tenths of Kelvin
        try:
            celsius = round((float(raw_temp) / 10.0) - 273.15, 1)
        except (TypeError, ValueError):
            continue
        rows.append({"zone": z.get("InstanceName", "?"), "temp_c": celsius})
        if celsius >= 85:
            res.findings.append(Finding(WARNING, "temps_high",
                                        {"zone": z.get("InstanceName", "?"), "temp": celsius}))
        else:
            res.findings.append(Finding(OK, "temps_ok",
                                        {"zone": z.get("InstanceName", "?"), "temp": celsius}))
    res.raw = rows
    if not rows:
        res.findings.append(Finding(INFO, "temps_unavailable"))
    res.meta = {"zone_count": len(rows)}
    return res


def collect_services() -> CategoryResult:
    """Services that are stopped but set to Automatic, plus recent failures from event log."""
    res = CategoryResult(key=CAT_SERVICES)
    stopped = _ps(
        "Get-CimInstance Win32_Service | Where-Object {$_.StartMode -eq 'Auto' -and "
        "$_.State -ne 'Running'} | Select-Object Name,DisplayName,State,StartMode | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    stopped = stopped if isinstance(stopped, list) else ([stopped] if stopped else [])
    rows = []
    for s in stopped or []:
        rows.append({"name": s.get("Name", "?"), "display": s.get("DisplayName", ""),
                     "state": s.get("State"), "startmode": s.get("StartMode")})
        res.findings.append(Finding(INFO, "services_stopped_auto",
                                    {"name": s.get("Name", "?")}))
    # recent service failures (last 48h) from System log
    failed = _ps(
        "$ev = Get-WinEvent -FilterHashtable @{LogName='System'; Id=7000,7001,7009,7034,7031,7036} "
        "-MaxEvents 50 -ErrorAction SilentlyContinue | "
        "Where-Object {$_.TimeCreated -gt (Get-Date).AddHours(-48)}; "
        "$ev | Select-Object Id,ProviderName,TimeCreated,@{n='Msg';e={$_.Message}} | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    failed = failed if isinstance(failed, list) else ([failed] if failed else [])
    res.raw = {"stopped_auto": rows, "recent_failures": failed or []}
    if failed:
        res.findings.append(Finding(WARNING if len(failed) >= 3 else INFO,
                                    "services_failed", {"n": len(failed)}))
    res.meta = {"stopped_auto_count": len(rows), "failure_count": len(failed or [])}
    return res


def collect_startup() -> CategoryResult:
    """Startup commands count."""
    res = CategoryResult(key=CAT_STARTUP)
    items = _ps(
        "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    items = items if isinstance(items, list) else ([items] if items else [])
    res.raw = items or []
    n = len(items or [])
    res.meta = {"count": n}
    if n >= 15:
        res.findings.append(Finding(WARNING, "startup_many", {"n": n}))
    elif n >= 8:
        res.findings.append(Finding(INFO, "startup_many", {"n": n}))
    else:
        res.findings.append(Finding(OK, "startup_ok", {"n": n}))
    return res


def collect_drivers() -> CategoryResult:
    """Signed drivers with problems (error / not OK)."""
    res = CategoryResult(key=CAT_DRIVERS)
    drv = _ps(
        "Get-CimInstance Win32_PnPSignedDriver | "
        "Where-Object {$_.Status -in @('Error','Degraded')} | "
        "Select-Object DeviceName,DriverVersion,Status,DriverProviderName | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    drv = drv if isinstance(drv, list) else ([drv] if drv else [])
    res.raw = drv or []
    n = len(drv or [])
    res.meta = {"problem_count": n}
    if n:
        res.findings.append(Finding(WARNING if n >= 3 else INFO,
                                    "drivers_problem", {"n": n}))
    else:
        res.findings.append(Finding(OK, "drivers_ok", {"n": 0}))
    return res


def collect_network() -> CategoryResult:
    """Adapters + default gateway presence."""
    res = CategoryResult(key=CAT_NETWORK)
    adapters = _ps(
        "Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed | "
        "ConvertTo-Json -Depth 4 -Compress;"
    )
    adapters = adapters if isinstance(adapters, list) else ([adapters] if adapters else [])
    gw = _ps(
        "Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object {$_.DefaultIPGateway} | "
        "Select-Object Description,DefaultIPGateway | ConvertTo-Json -Depth 4 -Compress;"
    )
    has_gw = bool(gw)
    rows = []
    for a in adapters or []:
        rows.append({"name": a.get("Name", "?"), "desc": a.get("InterfaceDescription", ""),
                     "status": a.get("Status"), "speed": a.get("LinkSpeed")})
        if str(a.get("Status", "")).lower() == "disabled":
            res.findings.append(Finding(INFO, "net_adapter_down",
                                        {"name": a.get("Name", "?")}))
    res.raw = {"adapters": rows, "has_gateway": has_gw}
    if not has_gw:
        res.findings.append(Finding(WARNING, "net_no_default_gateway"))
    res.meta = {"adapter_count": len(rows), "has_gateway": has_gw}
    return res


def collect_sysfiles() -> CategoryResult:
    """We do NOT run sfc/dism (admin + slow). We surface a recommendation to run them
    manually, and try to read the last CBS log status line for a hint."""
    res = CategoryResult(key=CAT_SYSFILES)
    last_status = None
    cbs = r"C:\Windows\Logs\CBS\CBS.log"
    try:
        if os.path.exists(cbs):
            # read tail without loading whole file
            size = os.path.getsize(cbs)
            with open(cbs, "rb") as fh:
                fh.seek(max(0, size - 8192))
                tail = fh.read().decode("utf-8", errors="replace")
            for marker in ("Repairing", "Verifying", "not find any", "corrupt", "repair failed"):
                if marker.lower() in tail.lower():
                    last_status = marker
                    break
    except OSError:
        last_status = None
    res.raw = [{"last_sfc_hint": last_status}]
    res.findings.append(Finding(INFO, "sysfiles_not_scanned"))
    if last_status:
        res.findings.append(Finding(INFO, "sysfiles_last_sfc_ok", {"status": last_status}))
    res.meta = {"last_status": last_status}
    return res


def collect_events() -> CategoryResult:
    """Critical / Error events in System + Application logs (last 48h)."""
    res = CategoryResult(key=CAT_EVENTS)
    ev = _ps(
        "Get-WinEvent -FilterHashtable @{LogName='System','Application'; Level=1,2; "
        "StartTime=(Get-Date).AddHours(-48)} -MaxEvents 200 -ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated,Id,ProviderName,LevelDisplayName,LogName,"
        "@{n='Msg';e={($_.Message -split \"`n\")[0]}} | ConvertTo-Json -Depth 4 -Compress;",
        timeout=90,
    )
    ev = ev if isinstance(ev, list) else ([ev] if ev else [])
    res.raw = ev or []
    n = len(ev or [])
    res.meta = {"count_48h": n}
    if n >= 10:
        res.findings.append(Finding(CRITICAL, "events_critical", {"n": n}))
    elif n >= 3:
        res.findings.append(Finding(WARNING, "events_critical", {"n": n}))
    elif n > 0:
        res.findings.append(Finding(INFO, "events_critical", {"n": n}))
    else:
        res.findings.append(Finding(OK, "events_ok", {"n": 0}))
    return res


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
COLLECTORS = {
    CAT_DISK: collect_disk,
    CAT_SPACE: collect_space,
    CAT_RAM: collect_ram,
    CAT_CPU: collect_cpu,
    CAT_TEMPS: collect_temps,
    CAT_SERVICES: collect_services,
    CAT_STARTUP: collect_startup,
    CAT_DRIVERS: collect_drivers,
    CAT_NETWORK: collect_network,
    CAT_SYSFILES: collect_sysfiles,
    CAT_EVENTS: collect_events,
}


def run_one(key: str) -> CategoryResult:
    fn = COLLECTORS.get(key)
    if not fn:
        return CategoryResult(key=key, error=f"unknown collector: {key}")
    return _safe(key, fn)


def run_all(progress_cb=None) -> Dict[str, CategoryResult]:
    """Run every collector in parallel (they are independent and read-only).

    progress_cb(key) is called as each collector is submitted. Collectors run
    in a thread pool so the 11 PowerShell subprocesses overlap instead of
    running sequentially (~2s instead of ~11s).
    """
    from concurrent.futures import ThreadPoolExecutor

    out: Dict[str, CategoryResult] = {}
    keys = list(ALL_CATEGORIES)
    for key in keys:
        if progress_cb:
            try:
                progress_cb(key)
            except Exception:  # noqa: BLE001
                pass
    with ThreadPoolExecutor(max_workers=min(8, len(keys))) as ex:
        futures = {ex.submit(run_one, key): key for key in keys}
        for fut in futures:
            out[futures[fut]] = fut.result()
    return out
