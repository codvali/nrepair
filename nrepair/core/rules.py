# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Rules engine: turns CategoryResults into prioritized Problems.

Each rule is a function (CategoryResult) -> Optional[Problem].
Rules only consume data already collected — they never run new commands.
"""

from typing import Callable, Dict, List, Optional

from .collectors import (
    CAT_DISK, CAT_SPACE, CAT_RAM, CAT_CPU, CAT_TEMPS, CAT_SERVICES,
    CAT_STARTUP, CAT_DRIVERS, CAT_NETWORK, CAT_SYSFILES, CAT_EVENTS,
)
from .model import (
    CategoryResult, Problem, Recommendation, Finding,
    OK, INFO, WARNING, CRITICAL, SEVERITY_ORDER,
)


def _rule_disk(res: CategoryResult) -> Optional[Problem]:
    crit = [f for f in res.findings if f.severity == CRITICAL]
    warn = [f for f in res.findings if f.severity == WARNING]
    if not (crit or warn):
        return None
    sev = CRITICAL if crit else WARNING
    # title = first non-OK finding message
    lead = (crit or warn)[0]
    return Problem(
        category=CAT_DISK, severity=sev,
        title_key=lead.message_key, title_fmt=lead.fmt,
        recommendations=[Recommendation(
            "disk_rec_backup" if sev == CRITICAL else "disk_rec_check",
            {},
            command="wmic diskdrive get status" if sev != CRITICAL else None,
        )] if False else [],
    )


def _rule_space(res: CategoryResult) -> Optional[Problem]:
    problems = [f for f in res.findings if f.is_problem()]
    if not problems:
        return None
    sev = CRITICAL if any(f.severity == CRITICAL for f in problems) else WARNING
    # use the worst drive as the headline
    worst = sorted(problems, key=lambda f: SEVERITY_ORDER[f.severity])[0]
    recs: List[Recommendation] = []
    # free space recommendation based on the worst drive
    vols = res.meta.get("volumes", [])
    if vols:
        # pick the volume matching the headline drive
        drive = worst.fmt.get("drive")
        match = next((v for v in vols if v.get("drive") == drive), None)
        if match:
            free_gb = match.get("free_gb", 0)
            need = max(10, int(20 - free_gb))
            recs.append(Recommendation("space_rec_free",
                                        {"gb": need, "drive": drive}))
    # update cache recommendation
    cache_gb = res.meta.get("update_cache_gb", 0.0)
    if cache_gb >= 1.0:
        recs.append(Recommendation("space_rec_update_cache", {"gb": cache_gb}))
    return Problem(
        category=CAT_SPACE, severity=sev,
        title_key=worst.message_key, title_fmt=worst.fmt,
        recommendations=recs,
    )


def _rule_ram(res: CategoryResult) -> Optional[Problem]:
    problems = [f for f in res.findings if f.is_problem()]
    if not problems:
        return None
    sev = CRITICAL if any(f.severity == CRITICAL for f in problems) else WARNING
    lead = problems[0]
    return Problem(
        category=CAT_RAM, severity=sev,
        title_key=lead.message_key, title_fmt=lead.fmt,
        recommendations=[Recommendation("ram_rec_close", {})],
    )


def _rule_cpu(res: CategoryResult) -> Optional[Problem]:
    problems = [f for f in res.findings if f.is_problem()]
    if not problems:
        return None
    lead = problems[0]
    return Problem(
        category=CAT_CPU, severity=WARNING,
        title_key=lead.message_key, title_fmt=lead.fmt,
        recommendations=[Recommendation("cpu_rec_investigate", {},
                                        command="taskmgr")],
    )


def _rule_temps(res: CategoryResult) -> Optional[Problem]:
    problems = [f for f in res.findings if f.is_problem()]
    if not problems:
        return None
    lead = problems[0]
    return Problem(
        category=CAT_TEMPS, severity=WARNING,
        title_key=lead.message_key, title_fmt=lead.fmt,
        recommendations=[Recommendation("temps_rec_dust", {})],
    )


def _rule_services(res: CategoryResult) -> Optional[Problem]:
    failures = res.meta.get("failure_count", 0)
    stopped = res.meta.get("stopped_auto_count", 0)
    if failures >= 3:
        sev = WARNING if failures < 10 else CRITICAL
        return Problem(
            category=CAT_SERVICES, severity=sev,
            title_key="services_failed", title_fmt={"n": failures},
            recommendations=[Recommendation("services_rec_restart", {},
                                            command="services.msc")],
        )
    if stopped > 0:
        return Problem(
            category=CAT_SERVICES, severity=INFO,
            title_key="services_stopped_auto", title_fmt={"name": f"{stopped} servicii"},
            recommendations=[Recommendation("services_rec_restart", {},
                                            command="services.msc")],
        )
    return None


def _rule_startup(res: CategoryResult) -> Optional[Problem]:
    n = res.meta.get("count", 0)
    if n >= 15:
        return Problem(
            category=CAT_STARTUP, severity=WARNING,
            title_key="startup_many", title_fmt={"n": n},
            recommendations=[Recommendation("startup_rec_disable", {},
                                            command="taskmgr /0 /startup")],
        )
    if n >= 8:
        return Problem(
            category=CAT_STARTUP, severity=INFO,
            title_key="startup_many", title_fmt={"n": n},
            recommendations=[Recommendation("startup_rec_disable", {},
                                            command="taskmgr /0 /startup")],
        )
    return None


def _rule_drivers(res: CategoryResult) -> Optional[Problem]:
    n = res.meta.get("problem_count", 0)
    if n <= 0:
        return None
    return Problem(
        category=CAT_DRIVERS, severity=WARNING if n >= 3 else INFO,
        title_key="drivers_problem", title_fmt={"n": n},
        recommendations=[Recommendation("drivers_rec_update", {},
                                        command="devmgmt.msc")],
    )


def _rule_network(res: CategoryResult) -> Optional[Problem]:
    if not res.meta.get("has_gateway", True):
        return Problem(
            category=CAT_NETWORK, severity=WARNING,
            title_key="net_no_default_gateway", title_fmt={},
            recommendations=[Recommendation("net_rec_enable",
                                            {"name": "adaptor"})],
        )
    down = [f for f in res.findings if f.message_key == "net_adapter_down"]
    if down:
        return Problem(
            category=CAT_NETWORK, severity=INFO,
            title_key="net_adapter_down", title_fmt=down[0].fmt,
            recommendations=[Recommendation("net_rec_enable", down[0].fmt)],
        )
    return None


def _rule_sysfiles(res: CategoryResult) -> Optional[Problem]:
    # Always surface the "run sfc manually" recommendation as INFO.
    return Problem(
        category=CAT_SYSFILES, severity=INFO,
        title_key="sysfiles_not_scanned", title_fmt={},
        recommendations=[Recommendation(
            "sysfiles_rec_run", {},
            command="sfc /scannow",
        )],
    )


def _rule_events(res: CategoryResult) -> Optional[Problem]:
    n = res.meta.get("count_48h", 0)
    if n <= 0:
        return None
    if n >= 10:
        sev = CRITICAL
    elif n >= 3:
        sev = WARNING
    else:
        sev = INFO
    return Problem(
        category=CAT_EVENTS, severity=sev,
        title_key="events_critical", title_fmt={"n": n},
        recommendations=[Recommendation("events_rec_review", {},
                                        command="eventvwr.msc")],
    )


RULES: Dict[str, Callable[[CategoryResult], Optional[Problem]]] = {
    CAT_DISK: _rule_disk,
    CAT_SPACE: _rule_space,
    CAT_RAM: _rule_ram,
    CAT_CPU: _rule_cpu,
    CAT_TEMPS: _rule_temps,
    CAT_SERVICES: _rule_services,
    CAT_STARTUP: _rule_startup,
    CAT_DRIVERS: _rule_drivers,
    CAT_NETWORK: _rule_network,
    CAT_SYSFILES: _rule_sysfiles,
    CAT_EVENTS: _rule_events,
}


def evaluate(results: Dict[str, CategoryResult]) -> List[Problem]:
    """Run all rules and return problems sorted by severity (critical first)."""
    problems: List[Problem] = []
    for key, rule in RULES.items():
        res = results.get(key)
        if res is None or res.error:
            continue
        p = rule(res)
        if p is not None:
            problems.append(p)
    problems.sort(key=lambda p: SEVERITY_ORDER.get(p.severity, 99))
    return problems
