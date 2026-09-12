# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Data model for nrepair diagnostics.

A Collector returns a CategoryResult containing:
  - raw: list of dict rows (for the per-category "details" view)
  - findings: list of Finding (normal / warning / critical) with i18n keys
  - meta: small dict of headline values (e.g. {"free_pct": 7})

The rules engine turns CategoryResults into Problems (with Recommendations).
Everything here is read-only metadata — no system mutation happens anywhere.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# severity constants
OK = "ok"
INFO = "info"
WARNING = "warning"
CRITICAL = "critical"

SEVERITY_ORDER = {CRITICAL: 0, WARNING: 1, INFO: 2, OK: 3}


@dataclass
class Finding:
    """A single observation from a collector, already human-described via i18n."""
    severity: str            # OK / INFO / WARNING / CRITICAL
    message_key: str         # i18n key
    fmt: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def is_problem(self) -> bool:
        return self.severity in (WARNING, CRITICAL)


@dataclass
class Recommendation:
    """A user-facing recommended action. Read-only: we never execute it."""
    message_key: str
    fmt: Dict[str, Any] = field(default_factory=dict)
    # optional command the user can copy-paste (never auto-run)
    command: Optional[str] = None


@dataclass
class Problem:
    """A problem surfaced to the Summary tab, with one or more recommendations."""
    category: str            # category key, e.g. "cat_disk"
    severity: str            # WARNING / CRITICAL
    title_key: str           # i18n key for the headline
    title_fmt: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Recommendation] = field(default_factory=list)


@dataclass
class CategoryResult:
    """Output of one collector."""
    key: str                 # e.g. "cat_disk"
    raw: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None  # if the collector itself crashed

    @property
    def worst_severity(self) -> str:
        worst = OK
        for f in self.findings:
            if SEVERITY_ORDER.get(f.severity, 99) < SEVERITY_ORDER.get(worst, 99):
                worst = f.severity
        return worst
