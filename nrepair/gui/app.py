# -*- coding: utf-8 -*-
#
# ╔══════════════════════════════════════════════════════════════╗
# ║                            NREPAIR                            ║
# ║                  Copyright © 2026 Valentin Condei            ║
# ╚══════════════════════════════════════════════════════════════╝
"""Tkinter GUI for nrepair.

Layout:
  - Top bar: language switch + Scan button + export buttons + status
  - Notebook:
      * Summary tab  -> prioritized problems + recommendations (mockup style)
      * one tab per category -> findings list + raw details
"""

import json
import os
import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from ..i18n.strings import t, SUPPORTED, DEFAULT
from ..core import collectors, rules, report
from ..core.model import CategoryResult, Problem, OK, INFO, WARNING, CRITICAL, SEVERITY_ORDER

SEV_COLOR = {
    CRITICAL: "#c0392b",
    WARNING: "#d68910",
    INFO: "#2980b9",
    OK: "#27ae60",
}


class NrepairGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(t("app_title", DEFAULT))
        self.root.geometry("980x640")
        self.root.minsize(860, 560)

        self.lang = tk.StringVar(value="ro")
        self.scanning = False
        self.results: dict = {}
        self.problems: list = []
        self.msg_queue: queue.Queue = queue.Queue()

        self._build_ui()
        self._drain_queue()
        self._retranslate()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)  # row 2 = notebook (expands)

        # ---- top bar (rows 0..1 inside `top`, which is root row 0) ----
        top = ttk.Frame(self.root, padding="10 10 10 8")
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)

        # row 0: title + subtitle (left) | language + About (right)
        head = ttk.Frame(top)
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(0, weight=1)

        self.lbl_title = ttk.Label(head, text=t("app_title", self._lang()),
                                   font=("Arial", 16, "bold"))
        self.lbl_title.grid(row=0, column=0, sticky="w")
        self.lbl_subtitle = ttk.Label(head, text=t("app_subtitle", self._lang()),
                                      font=("Arial", 9), foreground="gray")
        self.lbl_subtitle.grid(row=1, column=0, sticky="w", pady=(0, 8))

        right = ttk.Frame(head)
        right.grid(row=0, column=1, rowspan=2, sticky="ne")
        self.lbl_lang = ttk.Label(right, text=t("lang_label", self._lang()))
        self.lbl_lang.grid(row=0, column=0, padx=(0, 4))
        self.cmb_lang = ttk.Combobox(right, textvariable=self.lang, values=list(SUPPORTED),
                                     state="readonly", width=6)
        self.cmb_lang.grid(row=0, column=1, padx=(0, 8))
        self.cmb_lang.bind("<<ComboboxSelected>>", lambda _e: self._on_lang_change())
        # About/Donate as a colored tk.Button so it stands out (blue, white text)
        self.btn_about = tk.Button(right, text=t("btn_about", self._lang()),
                                   command=self._show_about, bg="#2980b9", fg="white",
                                   activebackground="#1f6d99", activeforeground="white",
                                   relief="flat", bd=0, padx=10, pady=3,
                                   font=("Arial", 9, "bold"), cursor="hand2")
        self.btn_about.grid(row=0, column=2)

        # row 1: action buttons (left) | export buttons (right)
        actions = ttk.Frame(top)
        actions.grid(row=1, column=0, sticky="ew")
        actions.columnconfigure(6, weight=1)

        self.btn_scan = ttk.Button(actions, text=t("btn_scan", self._lang()),
                                   command=self._start_scan)
        self.btn_scan.grid(row=0, column=0, padx=(0, 6))
        self.btn_copy = ttk.Button(actions, text=t("btn_copy", self._lang()),
                                   command=self._copy_summary)
        self.btn_copy.grid(row=0, column=1, padx=6)

        self.btn_html = ttk.Button(actions, text=t("btn_export_html", self._lang()),
                                   command=lambda: self._export("html"))
        self.btn_html.grid(row=0, column=3, padx=6, sticky="e")
        self.btn_json = ttk.Button(actions, text=t("btn_export_json", self._lang()),
                                   command=lambda: self._export("json"))
        self.btn_json.grid(row=0, column=4, padx=6, sticky="e")
        self.btn_md = ttk.Button(actions, text=t("btn_export_md", self._lang()),
                                 command=lambda: self._export("md"))
        self.btn_md.grid(row=0, column=5, padx=6, sticky="e")

        # row 2: status line (its own row, no overlap with notebook)
        self.lbl_status = ttk.Label(top, text=t("status_idle", self._lang()),
                                    foreground="blue", font=("Arial", 9))
        self.lbl_status.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # ---- notebook (root row 2, expands) ----
        self.nb = ttk.Notebook(self.root)
        self.nb.grid(row=2, column=0, sticky="nsew", padx=10, pady=(6, 10))

        self.summary_frame = ttk.Frame(self.nb, padding="8")
        self.nb.add(self.summary_frame, text=t("summary_tab", self._lang()))
        self._build_summary()

        self.cat_tabs: dict = {}
        for key in collectors.ALL_CATEGORIES:
            frame = ttk.Frame(self.nb, padding="8")
            self.nb.add(frame, text=t(key, self._lang()))
            self.cat_tabs[key] = frame
            self._build_cat_tab(key, frame)

    def _build_summary(self):
        f = self.summary_frame
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        self.lbl_summary_head = ttk.Label(f, text="", font=("Arial", 14, "bold"))
        self.lbl_summary_head.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.txt_summary = tk.Text(f, wrap="word", relief="flat",
                                   font=("Courier New", 9), padx=8, pady=8)
        self.txt_summary.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(f, command=self.txt_summary.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.txt_summary.configure(yscrollcommand=sb.set)
        self.txt_summary.configure(state="disabled")

    def _build_cat_tab(self, key, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        head = ttk.Label(frame, text=t(key, self._lang()), font=("Arial", 12, "bold"))
        head.grid(row=0, column=0, sticky="w")
        txt = tk.Text(frame, wrap="word", relief="flat",
                      font=("Courier New", 9), padx=8, pady=8)
        txt.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, command=txt.yview)
        sb.grid(row=1, column=1, sticky="ns")
        txt.configure(yscrollcommand=sb.set, state="disabled")
        self.cat_tabs[key] = (frame, txt, head)

    # ----------------------------------------------------------------- helpers
    def _lang(self) -> str:
        return self.lang.get() or DEFAULT

    def _on_lang_change(self):
        self._retranslate()

    def _retranslate(self):
        L = self._lang()
        self.root.title(t("app_title", L))
        self.lbl_title.configure(text=t("app_title", L))
        self.lbl_lang.configure(text=t("lang_label", L))
        self.btn_about.configure(text=t("btn_about", L))
        self.btn_scan.configure(text=t("btn_scan", L))
        self.btn_html.configure(text=t("btn_export_html", L))
        self.btn_json.configure(text=t("btn_export_json", L))
        self.btn_md.configure(text=t("btn_export_md", L))
        self.btn_copy.configure(text=t("btn_copy", L))
        self.lbl_subtitle.configure(text=t("app_subtitle", L))
        if not self.scanning:
            self.lbl_status.configure(text=t("status_idle", L), foreground="blue")
        # notebook tab labels
        self.nb.tab(self.summary_frame, text=t("summary_tab", L))
        for key in collectors.ALL_CATEGORIES:
            frame, txt, head = self.cat_tabs[key]
            self.nb.tab(frame, text=t(key, L))
            head.configure(text=t(key, L))
        # re-render content
        self._render_summary()
        self._render_categories()

    # ----------------------------------------------------------------- scan
    def _start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.btn_scan.configure(state="disabled")
        self.lbl_status.configure(text=t("status_scanning", self._lang(),
                                         cat=t("cat_disk", self._lang())),
                                  foreground="orange")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            self.results = collectors.run_all(progress_cb=self._on_progress)
            self.problems = rules.evaluate(self.results)
            self.msg_queue.put(("done", None))
        except Exception as e:  # noqa: BLE001
            self.msg_queue.put(("error", str(e)))

    def _on_progress(self, key):
        self.msg_queue.put(("progress", key))

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "progress":
                    self.lbl_status.configure(text=t("status_scanning", self._lang(),
                                                     cat=t(payload, self._lang())),
                                              foreground="orange")
                elif kind == "done":
                    self._render_summary()
                    self._render_categories()
                    n = len(self.problems)
                    if n:
                        self.lbl_status.configure(text=t("status_done", self._lang(), n=n),
                                                  foreground="green")
                    else:
                        self.lbl_status.configure(text=t("status_done_clean", self._lang()),
                                                  foreground="green")
                    self.scanning = False
                    self.btn_scan.configure(state="normal")
                elif kind == "error":
                    self.lbl_status.configure(text=f"Error: {payload}",
                                              foreground="red")
                    self.scanning = False
                    self.btn_scan.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(120, self._drain_queue)

    # ----------------------------------------------------------------- render
    def _render_summary(self):
        L = self._lang()
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("1.0", "end")
        if not self.results:
            self.txt_summary.insert("end", t("status_idle", L))
            self.txt_summary.configure(state="disabled")
            self.lbl_summary_head.configure(text="")
            return

        if self.problems:
            self.lbl_summary_head.configure(text=t("summary_problem_found", L),
                                            foreground=SEV_COLOR[CRITICAL])
        else:
            self.lbl_summary_head.configure(text=t("summary_no_problems", L),
                                            foreground=SEV_COLOR[OK])

        for p in self.problems:
            sev = p.severity
            tag = f"sev_{sev}"
            self.txt_summary.tag_configure(tag, foreground=SEV_COLOR.get(sev, "#000"),
                                           font=("Consolas", 10, "bold"))
            self.txt_summary.insert("end", f"[{t('sev_' + sev, L)}] ", tag)
            self.txt_summary.insert("end", f"{t(p.category, L)}\n")
            self.txt_summary.insert("end", f"  {t(p.title_key, L, **p.title_fmt)}\n\n")
            if p.recommendations:
                self.txt_summary.insert("end", f"  {t('summary_recommendation', L)}\n")
                for i, r in enumerate(p.recommendations, 1):
                    self.txt_summary.insert("end", f"   {i}. {t(r.message_key, L, **r.fmt)}\n")
                    if r.command:
                        self.txt_summary.insert("end", f"      > {r.command}\n")
                self.txt_summary.insert("end", "\n")
            # show-details hint: category tab name
            self.txt_summary.insert("end", f"  {t('btn_show_details', L)} → {t(p.category, L)}\n\n")
        self.txt_summary.configure(state="disabled")

    def _render_categories(self):
        L = self._lang()
        for key in collectors.ALL_CATEGORIES:
            frame, txt, head = self.cat_tabs[key]
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            res = self.results.get(key)
            if not res:
                txt.insert("end", t("status_idle", L))
                txt.configure(state="disabled")
                continue
            if res.error:
                txt.tag_configure("err", foreground=SEV_COLOR[CRITICAL])
                txt.insert("end", f"⚠ {res.error}\n", "err")
                txt.configure(state="disabled")
                continue
            # findings
            for f in res.findings:
                tag = f"sev_{f.severity}"
                txt.tag_configure(tag, foreground=SEV_COLOR.get(f.severity, "#000"),
                                  font=("Consolas", 10, "bold"))
                txt.insert("end", f"[{t('sev_' + f.severity, L) if f.severity in ('critical','warning','info') else 'OK'}] ", tag)
                txt.insert("end", f"{t(f.message_key, L, **f.fmt)}\n")
            # raw details
            txt.insert("end", "\n" + ("─" * 50) + "\n")
            txt.insert("end", f"{t('label_details', L)}\n\n")
            txt.insert("end", self._format_raw(res.raw))
            txt.configure(state="disabled")

    def _format_raw(self, raw) -> str:
        try:
            return json.dumps(raw, indent=2, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001
            return str(raw)

    # ----------------------------------------------------------------- export
    def _export(self, fmt):
        if not self.results:
            messagebox.showinfo(t("app_title", self._lang()), t("report_no_data", self._lang()))
            return
        folder = report.default_report_dir()
        ext = {"html": "html", "json": "json", "md": "md"}[fmt]
        path = report.unique_path(folder, ext)
        try:
            if fmt == "html":
                report.export_html(self.results, self.problems, self._lang(), path)
            elif fmt == "json":
                report.export_json(self.results, self.problems, self._lang(), path)
            else:
                report.export_markdown(self.results, self.problems, self._lang(), path)
            self.lbl_status.configure(text=t("export_saved", self._lang(), path=path),
                                      foreground="green")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(t("app_title", self._lang()),
                                 t("export_failed", self._lang(), err=e))

    def _copy_summary(self):
        if not self.problems:
            return
        L = self._lang()
        lines = [t("summary_problem_found", L), ""]
        for p in self.problems:
            lines.append(f"[{t('sev_'+p.severity, L)}] {t(p.category, L)}: "
                         f"{t(p.title_key, L, **p.title_fmt)}")
            for i, r in enumerate(p.recommendations, 1):
                lines.append(f"  {i}. {t(r.message_key, L, **r.fmt)}")
                if r.command:
                    lines.append(f"     > {r.command}")
            lines.append("")
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self.lbl_status.configure(text=t("copied", self._lang()), foreground="green")

    # ----------------------------------------------------------------- about / donate
    PAYPAL_BASE = "https://www.paypal.com/paypalme/ValentinCondei"
    SITE_EN = "https://voensys.com/vaos/en/utilities/nrepair"
    SITE_RO = "https://voensys.com/vaos/ro/utilitati/nrepair"
    UTILS_EN = "https://voensys.com/vaos/en/utilities/"
    UTILS_RO = "https://voensys.com/vaos/ro/utilitati/"

    def _show_about(self):
        L = self._lang()
        about = tk.Toplevel(self.root)
        about.title(t("about_title", L))
        about.geometry("560x660")
        about.resizable(False, False)
        about.transient(self.root)

        f = ttk.Frame(about, padding="20")
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="nrepair", font=("Arial", 16, "bold")).pack(pady=(0, 2))
        ttk.Label(f, text=t("about_tagline", L), font=("Arial", 10)).pack(pady=(0, 2))
        ttk.Label(f, text=t("about_readonly_badge", L), font=("Arial", 9),
                  foreground="green").pack(pady=(0, 15))

        ttk.Label(f, text=t("about_author_h", L), font=("Arial", 9, "bold")).pack()
        ttk.Label(f, text=t("about_author_name", L), font=("Arial", 11, "bold")).pack()
        ttk.Label(f, text=t("about_email", L)).pack()
        ttk.Label(f, text=t("about_company", L), foreground="blue").pack()

        ttk.Label(f, text=t("about_links_h", L), font=("Arial", 9, "bold")).pack(pady=(10, 2))
        links = ttk.Frame(f)
        links.pack()
        for label_key, url in (("about_link_en", self.SITE_EN), ("about_link_ro", self.SITE_RO)):
            lbl = ttk.Label(links, text=t(label_key, L), foreground="blue",
                            cursor="hand2", font=("Arial", 8, "underline"))
            lbl.pack(side="left", padx=8)
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        more = ttk.Label(f, text=t("about_more_utils", L), foreground="gray",
                         cursor="hand2", font=("Arial", 8))
        more.pack(pady=(4, 0))
        more.bind("<Button-1>", lambda e: webbrowser.open(self.UTILS_EN if L == "en" else self.UTILS_RO))

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=12)

        ttk.Label(f, text=t("about_libs_h", L), font=("Arial", 9, "bold")).pack()
        ttk.Label(f, text=t("about_libs_body", L), justify="center",
                  font=("Courier New", 8)).pack()

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=12)

        ttk.Label(f, text=t("about_donate_h", L), font=("Arial", 9, "bold")).pack()
        ttk.Label(f, text=t("about_donate_msg", L), font=("Arial", 9)).pack(pady=(0, 8))

        amounts = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50]
        btn_frame = ttk.Frame(f)
        btn_frame.pack()
        for i, amt in enumerate(amounts):
            url = f"{self.PAYPAL_BASE}/{amt}"
            b = ttk.Button(btn_frame, text=f"{amt} EUR", width=9,
                           command=lambda u=url: self._donate(u))
            b.grid(row=i // 5, column=i % 5, padx=3, pady=3)

        link = ttk.Label(f, text=self.PAYPAL_BASE, foreground="blue",
                         cursor="hand2", font=("Arial", 8, "underline"))
        link.pack(pady=(8, 0))
        link.bind("<Button-1>", lambda e: webbrowser.open(self.PAYPAL_BASE))

        ttk.Button(f, text=t("about_close", L), command=about.destroy).pack(pady=(15, 0))

    def _donate(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:  # noqa: BLE001
            messagebox.showinfo("Donate", f"Visit: {url}")


def launch():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:  # noqa: BLE001
        pass
    NrepairGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
