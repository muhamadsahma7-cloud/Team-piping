# tabs/irn_report_tab.py

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

def build_tab(parent, permissions):
    frame = tk.Frame(parent)

    # ───── Left Panel ─────
    left_panel = tk.Frame(frame)
    left_panel.pack(side="left", padx=10, pady=10, fill="y")

    tk.Label(left_panel, text="Type ISO DWG NO:").grid(row=0, column=0, sticky="w")
    iso_var = tk.StringVar()
    iso_entry = tk.Entry(left_panel, textvariable=iso_var, width=30)
    iso_entry.grid(row=1, column=0, sticky="w")

    iso_listbox = tk.Listbox(left_panel, width=30, height=5)
    iso_listbox.grid(row=2, column=0, sticky="w")
    scroll = tk.Scrollbar(left_panel, orient="vertical", command=iso_listbox.yview)
    iso_listbox.configure(yscrollcommand=scroll.set)
    scroll.grid(row=2, column=1, sticky="ns")

    tk.Label(left_panel, text="PAGE NO:").grid(row=3, column=0, sticky="w", pady=(10, 0))
    page_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    page_combo.grid(row=4, column=0, sticky="w")

    tk.Label(left_panel, text="SPOOL NO:").grid(row=5, column=0, sticky="w", pady=(10, 0))
    spool_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    spool_combo.grid(row=6, column=0, sticky="w")

    today = datetime.today().strftime("%Y-%m-%d")

    irn_date_var = tk.StringVar(value=today)
    irn_report_var = tk.StringVar()

    def make_input_row(parent, row, label, var, field, icon):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(parent, textvariable=var, width=24)
        entry.grid(row=row, column=1, sticky="w", padx=(0, 5))
        btn = tk.Button(parent, text=icon + " Save", bg="#1976D2", fg="white", command=lambda: update_field(field, var.get()))
        btn.grid(row=row, column=2, sticky="w")
    
    make_input_row(left_panel, 7, "IRN DATE:", irn_date_var, "irn_date", "💾")
    make_input_row(left_panel, 8, "IRN REPORT NO:", irn_report_var, "irn_report_no", "📄")

    # ───── Right Panel ─────
    right_panel = tk.Frame(frame)
    right_panel.pack(side="left", padx=10, pady=10, fill="both", expand=True)

    tk.Label(right_panel, text="Joint Detail Info", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    readonly_text = tk.Text(right_panel, width=80, height=18, bg="#f4f4f4")
    readonly_text.pack(fill="both", expand=True)

    # ───── Database ─────
    conn = sqlite3.connect("database/spool_tracking.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
    all_iso_list = sorted(r[0] for r in cur.fetchall())
    cur.execute("SELECT DISTINCT iso_dwg_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S'")
    iso_page_spool_list = cur.fetchall()
    conn.close()

    # ───── Logic ─────
    def update_iso_list(*args):
        typed = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso_list:
            if typed in iso.lower():
                iso_listbox.insert(tk.END, iso)

    def on_iso_select(e):
        sel = iso_listbox.curselection()
        if not sel:
            return
        selected_iso = iso_listbox.get(sel[0])
        iso_var.set(selected_iso)
        refresh_page_combo()

    def refresh_page_combo():
        iso = iso_var.get().strip()
        pages = sorted(set(p for i, p, _ in iso_page_spool_list if i == iso))
        page_combo['values'] = pages
        page_combo.set('')
        spool_combo.set('')
        readonly_text.delete("1.0", tk.END)

    def refresh_spools(event=None):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spools = sorted(set(s for i, p, s in iso_page_spool_list if i == iso and p == page))
        spool_combo['values'] = spools
        spool_combo.set('')
        readonly_text.delete("1.0", tk.END)

    def show_joint_details(event=None):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not iso or not page or not spool:
            return
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT joint_no, item_1, sch_rating_1, item_2, sch_rating_2,
                   heat_no_1, heat_no_2, irn_date, irn_report_no
            FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND shop_field = 'S'
        """, (iso, page, spool))
        rows = cur.fetchall()
        conn.close()
        readonly_text.delete("1.0", tk.END)
        for r in rows:
            readonly_text.insert(tk.END, f"Joint {r[0]}:\n")
            readonly_text.insert(tk.END, f"  ITEM 1: {r[1]} | SCH 1: {r[2]}\n")
            readonly_text.insert(tk.END, f"  ITEM 2: {r[3]} | SCH 2: {r[4]}\n")
            readonly_text.insert(tk.END, f"  HEAT NO. 1: {r[5]} | HEAT NO. 2: {r[6]}\n")
            readonly_text.insert(tk.END, f"  IRN DATE: {r[7] or '-'} | IRN REPORT NO: {r[8] or '-'}\n\n")

    def update_field(field, value):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not iso or not page or not spool:
            messagebox.showerror("Error", "Please complete ISO, PAGE, and SPOOL selections.")
            return
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE spools
            SET {field} = ?
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND shop_field = 'S'
        """, (value, iso, page, spool))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"{field.replace('_',' ').title()} updated for spool {spool}.")
        show_joint_details()

    # ───── Bindings ─────
    iso_var.trace_add("write", update_iso_list)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    page_combo.bind("<<ComboboxSelected>>", refresh_spools)
    spool_combo.bind("<<ComboboxSelected>>", show_joint_details)

    for iso in all_iso_list:
        iso_listbox.insert(tk.END, iso)

    return frame
