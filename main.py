# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""nrepair entry point.

  python main.py            -> launch GUI
  python main.py --cli      -> run a scan in the terminal and print summary
  python main.py --cli --lang en --export-md report.md
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="nrepair",
                                     description="PC diagnostic for normal users (read-only).")
    parser.add_argument("--cli", action="store_true",
                        help="run in terminal instead of GUI")
    parser.add_argument("--lang", choices=("ro", "en"), default="ro",
                        help="output language (default: ro)")
    parser.add_argument("--export-md", metavar="PATH", help="write a Markdown report")
    parser.add_argument("--export-html", metavar="PATH", help="write an HTML report")
    parser.add_argument("--export-json", metavar="PATH", help="write a JSON report")
    args = parser.parse_args()

    if not args.cli:
        from nrepair.gui.app import launch
        launch()
        return

    # ---- CLI mode ----
    from nrepair.i18n.strings import t
    from nrepair.core import collectors, rules, report

    lang = args.lang
    print(f"nrepair — {t('app_title', lang)}")
    print(t("app_subtitle", lang))
    print()

    def progress(key):
        print(f"  {t('status_scanning', lang, cat=t(key, lang))}")

    results = collectors.run_all(progress_cb=progress)
    problems = rules.evaluate(results)
    print()
    if problems:
        print(f"=== {t('summary_problem_found', lang)} ===")
        for p in problems:
            sev = t("sev_" + p.severity, lang) if p.severity in ("critical", "warning", "info") else p.severity.upper()
            print(f"\n[{sev}] {t(p.category, lang)}")
            print(f"  {t(p.title_key, lang, **p.title_fmt)}")
            if p.recommendations:
                print(f"  {t('summary_recommendation', lang)}")
                for i, r in enumerate(p.recommendations, 1):
                    print(f"   {i}. {t(r.message_key, lang, **r.fmt)}")
                    if r.command:
                        print(f"      > {r.command}")
    else:
        print(f"=== {t('summary_no_problems', lang)} ===")

    if args.export_md:
        report.export_markdown(results, problems, lang, args.export_md)
        print(f"\n{t('export_saved', lang, path=args.export_md)}")
    if args.export_html:
        report.export_html(results, problems, lang, args.export_html)
        print(f"\n{t('export_saved', lang, path=args.export_html)}")
    if args.export_json:
        report.export_json(results, problems, lang, args.export_json)
        print(f"\n{t('export_saved', lang, path=args.export_json)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
