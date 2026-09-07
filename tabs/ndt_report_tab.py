# tabs/ndt_report_tab.py

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = tk.Frame(parent)

    # ─── Left and Right Panels ───────────────────────────
    left_panel = tk.Frame(frame)
    left_panel.pack(side="left", fill="y", padx=10, pady=10)

    right_panel = tk.Frame(frame)
    right_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    today = datetime.today().strftime("%Y-%m-%d")

    # ─── ISO DWG NO Filter ───────────────────────────────
    tk.Label(left_panel, text="Type ISO DWG NO:").pack(anchor="w")
    iso_var = tk.StringVar()
    tk.Entry(left_panel, textvariable=iso_var, width=30).pack(anchor="w", pady=(0, 5))

    iso_listbox = tk.Listbox(left_panel, height=5, width=30)
    iso_listbox.pack(anchor="w", fill="x")
    iso_scroll = tk.Scrollbar(left_panel, orient="vertical", command=iso_listbox.yview)
    iso_listbox.configure(yscrollcommand=iso_scroll.set)
    iso_scroll.place(in_=iso_listbox, relx=1.0, rely=0, relheight=1.0, anchor='ne')

    # ─── PAGE NO Filter ──────────────────────────────────
    tk.Label(left_panel, text="PAGE NO (iso_run_no):").pack(anchor="w", pady=(10, 0))
    page_combo = ttk.Combobox(left_panel, width=27, state="readonly")
    page_combo.pack(anchor="w", pady=(0, 5))

    # ─── Spool & Joint ───────────────────────────────────
    tk.Label(left_panel, text="DWG SPOOL NO:").pack(anchor="w")
    spool_combo = ttk.Combobox(left_panel, width=27, state="readonly")
    spool_combo.pack(anchor="w", pady=(0, 5))

    tk.Label(left_panel, text="JOINT NO (shop weld only):").pack(anchor="w")
    joint_listbox = tk.Listbox(left_panel, selectmode=tk.MULTIPLE, width=30, height=6)
    joint_listbox.pack(anchor="w", fill="x", pady=(0, 5))

    # ─── Inputs ──────────────────────────────────────────
    input_frame = tk.Frame(left_panel)
    input_frame.pack(anchor="w", pady=5)

    def make_input_row(row, label1, var1, label2, var2, btn_text, field1, field2):
        tk.Label(input_frame, text=label1).grid(row=row, column=0, sticky="w")
        tk.Entry(input_frame, textvariable=var1, width=20).grid(row=row, column=1, padx=5)
        tk.Label(input_frame, text=label2).grid(row=row, column=2, sticky="w")
        tk.Entry(input_frame, textvariable=var2, width=20).grid(row=row, column=3, padx=5)
        tk.Button(input_frame, text=f"💾 {btn_text}", width=15, bg="#4CAF50", fg="white",
                  command=lambda: update_fields([field1, field2], [var1.get(), var2.get()])
        ).grid(row=row, column=4, padx=5)

    mpi_pt_date_var = tk.StringVar(value=today)
    mpi_pt_report_var = tk.StringVar()
    make_input_row(0, "MPI/PT DATE:", mpi_pt_date_var, "REPORT NO:", mpi_pt_report_var,
                   "MPI/PT", "mpi_pt_date", "mpi_pt_report_no")

    hardness_date_var = tk.StringVar(value=today)
    hardness_report_var = tk.StringVar()
    make_input_row(1, "HARDNESS DATE:", hardness_date_var, "REPORT NO:", hardness_report_var,
                   "Hardness", "hardness_date", "hardness_report_no")

    pmi_date_var = tk.StringVar(value=today)
    pmi_report_var = tk.StringVar()
    make_input_row(2, "PMI DATE:", pmi_date_var, "REPORT NO:", pmi_report_var,
                   "PMI", "pmi_date", "pmi_report_no")

    ferrite_date_var = tk.StringVar(value=today)
    ferrite_report_var = tk.StringVar()
    make_input_row(3, "FERRITE DATE:", ferrite_date_var, "REPORT NO:", ferrite_report_var,
                   "Ferrite", "ferrite_date", "ferrite_report_no")

    # ─── Right Panel: Joint Details ──────────────────────
    readonly_text = tk.Text(right_panel, width=90, height=28, bg="#f4f4f4", font=("Courier New", 9))
    readonly_text.pack(fill="both", expand=True)

    # ─── Load ISO DWG NOs ────────────────────────────────
    def load_iso_list():
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT iso_dwg_no FROM spools
            WHERE shop_field = 'S' AND (pwht = 'NO' OR (pwht = 'YES' AND rt_asr_date IS NOT NULL))
        """)
        iso_list = sorted(r[0] for r in cursor.fetchall())
        conn.close()
        for iso in iso_list:
            iso_listbox.insert(tk.END, iso)
        return iso_list

    all_iso_list = load_iso_list()

    # ─── Events and Helpers ──────────────────────────────
    def update_iso_list(*args):
        typed = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso_list:
            if typed in iso.lower():
                iso_listbox.insert(tk.END, iso)

    def on_iso_select(event):
        sel = iso_listbox.curselection()
        if not sel: return
        iso = iso_listbox.get(sel[0])
        iso_var.set(iso)
        iso_listbox.delete(0, tk.END)
        refresh_pages()

    def refresh_pages():
        iso = iso_var.get().strip()
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute("""SELECT DISTINCT iso_run_no FROM spools WHERE iso_dwg_no = ? AND shop_field = 'S'""", (iso,))
        pages = [r[0] for r in cur.fetchall()]
        conn.close()
        page_combo['values'] = pages
        page_combo.set('')
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def refresh_spools(event=None):
        iso, page = iso_var.get().strip(), page_combo.get().strip()
        if not iso or not page: return
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT dwg_spool_no FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND shop_field = 'S'
              AND (pwht = 'NO' OR (pwht = 'YES' AND rt_asr_date IS NOT NULL))
        """, (iso, page))
        spools = [r[0] for r in cur.fetchall()]
        conn.close()
        spool_combo['values'] = spools
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def refresh_joints(event=None):
        iso, page, spool = iso_var.get().strip(), page_combo.get().strip(), spool_combo.get().strip()
        if not iso or not page or not spool: return
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT joint_no FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND shop_field = 'S'
              AND (pwht = 'NO' OR (pwht = 'YES' AND rt_asr_date IS NOT NULL))
        """, (iso, page, spool))
        joints = [r[0] for r in cur.fetchall()]
        conn.close()
        joint_listbox.delete(0, tk.END)
        for j in joints:
            joint_listbox.insert(tk.END, j)
        readonly_text.delete("1.0", tk.END)

    def show_joint_info(event=None):
        iso, page, spool = iso_var.get().strip(), page_combo.get().strip(), spool_combo.get().strip()
        sel = joint_listbox.curselection()
        if not (iso and page and spool and sel): return
        joints = [joint_listbox.get(i) for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        out = ""
        for j in joints:
            cur.execute("""
                SELECT item_1, sch_rating_1, item_2, sch_rating_2,
                       mpi_pt_date, mpi_pt_report_no,
                       hardness_date, hardness_report_no,
                       pmi_date, pmi_report_no,
                       ferrite_date, ferrite_report_no
                FROM spools
                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (iso, page, spool, j))
            row = cur.fetchone()
            if row:
                out += f"Joint {j}:\n"
                out += f"  ITEM 1: {row[0]} | SCH/RATING 1: {row[1]}\n"
                out += f"  ITEM 2: {row[2]} | SCH/RATING 2: {row[3]}\n"
                out += f"  MPI/PT     : {row[4] or '-'} | {row[5] or '-'}\n"
                out += f"  HARDNESS   : {row[6] or '-'} | {row[7] or '-'}\n"
                out += f"  PMI        : {row[8] or '-'} | {row[9] or '-'}\n"
                out += f"  FERRITE    : {row[10] or '-'} | {row[11] or '-'}\n\n"
        conn.close()
        readonly_text.delete("1.0", tk.END)
        readonly_text.insert(tk.END, out.strip())

    def update_fields(fields, values):
        iso, page, spool = iso_var.get().strip(), page_combo.get().strip(), spool_combo.get().strip()
        sel = joint_listbox.curselection()
        if not iso or not page or not spool or not sel:
            messagebox.showerror("Error", "Please select ISO, Page, Spool, and at least one Joint.")
            return
        joints = [joint_listbox.get(i) for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        for j in joints:
            for f, v in zip(fields, values):
                cur.execute(f"""UPDATE spools SET {f} = ? 
                                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'""",
                            (v, iso, page, spool, j))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"{', '.join(fields).upper()} updated for {len(joints)} joint(s).")
        show_joint_info()

    # ─── Bindings ───────────────────────────────────────
    iso_var.trace_add("write", update_iso_list)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    page_combo.bind("<<ComboboxSelected>>", refresh_spools)
    spool_combo.bind("<<ComboboxSelected>>", refresh_joints)
    joint_listbox.bind("<<ListboxSelect>>", show_joint_info)

    return frame
