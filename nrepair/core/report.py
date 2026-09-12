# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Report exporters: HTML, JSON, Markdown.

All exporters consume the same ScanResult snapshot (results + problems + lang).
"""

import html
import json
import os
import platform
from datetime import datetime
from typing import Dict, List

from ..i18n.strings import t
from .collectors import ALL_CATEGORIES
from .model import CategoryResult, Problem, SEVERITY_ORDER


def _sev_label(sev: str, lang: str) -> str:
    return t(f"sev_{sev}", lang) if sev in ("critical", "warning", "info") else sev.upper()


def _serialize_results(results: Dict[str, CategoryResult]) -> Dict:
    out = {}
    for key, res in results.items():
        out[key] = {
            "error": res.error,
            "meta": res.meta,
            "findings": [
                {"severity": f.severity, "message": f.message_key, "fmt": f.fmt}
                for f in res.findings
            ],
            "raw": res.raw,
        }
    return out


def export_json(results, problems, lang, path) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {
        "tool": "nrepair",
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "machine": platform.node(),
        "os": platform.platform(),
        "language": lang,
        "problems": [
            {
                "category": p.category,
                "severity": p.severity,
                "title_key": p.title_key,
                "title_fmt": p.title_fmt,
                "recommendations": [
                    {"message_key": r.message_key, "fmt": r.fmt, "command": r.command}
                    for r in p.recommendations
                ],
            }
            for p in problems
        ],
        "categories": _serialize_results(results),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def export_markdown(results, problems, lang, path) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lines: List[str] = []
    lines.append(f"# {t('report_title', lang)}")
    lines.append("")
    lines.append(f"- {t('report_generated', lang)}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- {t('report_machine', lang)}: {platform.node()} ({platform.platform()})")
    lines.append("")
    lines.append(f"## {t('report_problems', lang)}")
    if not problems:
        lines.append(f"_{t('summary_no_problems', lang)}_")
    else:
        for p in problems:
            lines.append(f"### [{_sev_label(p.severity, lang)}] {t(p.category, lang)}")
            lines.append("")
            lines.append("- " + t(p.title_key, lang, **p.title_fmt))
            if p.recommendations:
                lines.append("")
                lines.append(f"**{t('summary_recommendation', lang)}**")
                for r in p.recommendations:
                    lines.append(f"1. {t(r.message_key, lang, **r.fmt)}")
                    if r.command:
                        lines.append(f"   ```")
                        lines.append(f"   {r.command}")
                        lines.append(f"   ```")
            lines.append("")
    lines.append(f"## {t('report_categories', lang)}")
    for key in ALL_CATEGORIES:
        res = results.get(key)
        if not res:
            continue
        lines.append(f"### {t(key, lang)}")
        if res.error:
            lines.append(f"- ⚠ {res.error}")
            continue
        for f in res.findings:
            mark = {"critical": "🔴", "warning": "🟡", "info": "🔵", "ok": "🟢"}.get(f.severity, "•")
            lines.append(f"- {mark} {t(f.message_key, lang, **f.fmt)}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


_HTML_TEMPLATE = """<!doctype html>
<html lang="{lang_code}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 24px; color: #1b1b1b; }}
  h1 {{ font-size: 22px; }}
  h2 {{ font-size: 18px; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 28px; }}
  h3 {{ font-size: 15px; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 12px; margin-bottom: 16px; }}
  .sev {{ display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; color: #fff; }}
  .sev-critical {{ background: #c0392b; }}
  .sev-warning  {{ background: #d68910; }}
  .sev-info     {{ background: #2980b9; }}
  .sev-ok       {{ background: #27ae60; }}
  .problem {{ border-left: 3px solid #c0392b; padding: 8px 12px; margin: 8px 0; background: #fdf3f2; }}
  .problem.warning {{ border-color: #d68910; background: #fef9e7; }}
  .problem.info {{ border-color: #2980b9; background: #ebf5fb; }}
  .rec {{ margin: 4px 0 4px 16px; }}
  code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 3px; font-size: 12px; }}
  ul.cat {{ list-style: none; padding-left: 0; }}
  ul.cat li {{ padding: 2px 0; }}
  .ok {{ color: #27ae60; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">{generated} {gen_val}<br>{machine} {mach_val}<br>{os_label}: {os_val}</div>
<h2>{problems_h}</h2>
{problems_body}
<h2>{categories_h}</h2>
{categories_body}
</body>
</html>
"""


def export_html(results, problems, lang, path) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lang_code = "ro" if lang == "ro" else "en"
    problems_body = []
    if not problems:
        problems_body.append(f"<p><em>{html.escape(t('summary_no_problems', lang))}</em></p>")
    for p in problems:
        cls = f"problem {p.severity}"
        sev = f'<span class="sev sev-{p.severity}">{_sev_label(p.severity, lang)}</span>'
        title = html.escape(t(p.title_key, lang, **p.title_fmt))
        body = [f'<div class="{cls}">{sev} <strong>{html.escape(t(p.category, lang))}</strong> — {title}']
        if p.recommendations:
            body.append(f'<div class="rec"><strong>{html.escape(t("summary_recommendation", lang))}</strong><ol>')
            for r in p.recommendations:
                body.append(f"<li>{html.escape(t(r.message_key, lang, **r.fmt))}")
                if r.command:
                    body.append(f"<br><code>{html.escape(r.command)}</code>")
                body.append("</li>")
            body.append("</ol></div>")
        body.append("</div>")
        problems_body.append("".join(body))

    categories_body = []
    for key in ALL_CATEGORIES:
        res = results.get(key)
        if not res:
            continue
        categories_body.append(f"<h3>{html.escape(t(key, lang))}</h3>")
        if res.error:
            categories_body.append(f'<ul class="cat"><li>⚠ {html.escape(res.error)}</li></ul>')
            continue
        items = []
        for f in res.findings:
            cls = f"sev sev-{f.severity}"
            sev = f'<span class="{cls}">{_sev_label(f.severity, lang)}</span>'
            items.append(f"<li>{sev} {html.escape(t(f.message_key, lang, **f.fmt))}</li>")
        categories_body.append(f'<ul class="cat">{"".join(items)}</ul>')

    doc = _HTML_TEMPLATE.format(
        lang_code=lang_code,
        title=html.escape(t("report_title", lang)),
        generated=html.escape(t("report_generated", lang) + ":"),
        gen_val=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        machine=html.escape(t("report_machine", lang) + ":"),
        mach_val=html.escape(platform.node()),
        os_label="OS",
        os_val=html.escape(platform.platform()),
        problems_h=html.escape(t("report_problems", lang)),
        problems_body="".join(problems_body),
        categories_h=html.escape(t("report_categories", lang)),
        categories_body="".join(categories_body),
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return path


def default_report_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), "nrepair_reports")
    os.makedirs(base, exist_ok=True)
    return base


def unique_path(folder: str, ext: str, prefix: str = "nrepair") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"{prefix}_{ts}.{ext}")
