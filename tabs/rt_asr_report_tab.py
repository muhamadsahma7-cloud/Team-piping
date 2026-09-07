# tabs/rt_asr_report_tab.py

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = ttk.Frame(parent)

    # ─── Layout Frames ──────────────────────────────────────────────────────
    left = ttk.Frame(frame)
    left.pack(side="left", fill="y", padx=10, pady=10)

    right = ttk.Frame(frame)
    right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    # ─── Preload ISO DWG NO list ────────────────────────────────────────────
    conn = sqlite3.connect("database/spool_tracking.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iso_dwg_no
        FROM spools
        WHERE shop_field = 'S' AND pwht = 'YES'
        GROUP BY iso_dwg_no
        HAVING COUNT(*) = SUM(CASE WHEN pwht_date IS NOT NULL THEN 1 ELSE 0 END)
    """)
    all_iso_list = sorted([r[0] for r in cursor.fetchall()])
    conn.close()

    # ─── Widgets - Left Panel ───────────────────────────────────────────────
    tk.Label(left, text="Type ISO DWG NO:").pack(anchor="w")
    iso_var = tk.StringVar()
    tk.Entry(left, textvariable=iso_var, width=30).pack(anchor="w", pady=2)

    iso_listbox = tk.Listbox(left, height=6, width=30)
    iso_listbox.pack(anchor="w", pady=2)
    scroll = ttk.Scrollbar(left, orient="vertical", command=iso_listbox.yview)
    iso_listbox.config(yscrollcommand=scroll.set)
    scroll.place(in_=iso_listbox, relx=1.0, rely=0, relheight=1.0)

    tk.Label(left, text="PAGE NO:").pack(anchor="w", pady=(10, 0))
    page_var = tk.StringVar()
    page_combo = ttk.Combobox(left, textvariable=page_var, width=28, state="readonly")
    page_combo.pack(anchor="w", pady=2)

    tk.Label(left, text="DWG SPOOL NO:").pack(anchor="w", pady=(10, 0))
    spool_var = tk.StringVar()
    spool_combo = ttk.Combobox(left, textvariable=spool_var, width=28, state="readonly")
    spool_combo.pack(anchor="w", pady=2)

    tk.Label(left, text="JOINT NO (shop weld only):").pack(anchor="w", pady=(10, 0))
    joint_listbox = tk.Listbox(left, selectmode=tk.MULTIPLE, width=30, height=6)
    joint_listbox.pack(anchor="w", pady=2)

    # ─── Widgets - Right Panel ──────────────────────────────────────────────
    today = datetime.today().strftime("%Y-%m-%d")

    ttk.Label(right, text="RT ASR DATE:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    rt_asr_date_var = tk.StringVar(value=today)
    tk.Entry(right, textvariable=rt_asr_date_var, width=30).grid(row=0, column=1, sticky="w", pady=5)
    tk.Button(right, text="💾 Save", width=10, bg="#1976D2", fg="white",
              command=lambda: update_field("rt_asr_date", rt_asr_date_var.get())).grid(row=0, column=2, padx=5)

    ttk.Label(right, text="RT ASR REPORT NO:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    rt_asr_report_var = tk.StringVar()
    tk.Entry(right, textvariable=rt_asr_report_var, width=30).grid(row=1, column=1, sticky="w", pady=5)
    tk.Button(right, text="💾 Save", width=10, bg="#F57C00", fg="white",
              command=lambda: update_field("rt_asr_report_no", rt_asr_report_var.get())).grid(row=1, column=2, padx=5)

    tk.Button(right, text="🔍 View Joint Details", width=30,
              command=lambda: show_joint_info()).grid(row=2, column=0, columnspan=3, pady=10)

    joint_text = tk.Text(right, width=80, height=12, bg="#f4f4f4")
    joint_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    # ─── Functions ──────────────────────────────────────────────────────────
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
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT iso_run_no FROM spools WHERE iso_dwg_no = ? AND shop_field = 'S' AND pwht = 'YES'", (iso,))
        pages = [r[0] for r in cursor.fetchall()]
        conn.close()
        page_combo['values'] = pages
        page_combo.set('')
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        joint_text.delete("1.0", tk.END)

    def refresh_spools(*args):
        iso = iso_var.get().strip()
        page = page_var.get().strip()
        if not iso or not page: return
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT dwg_spool_no FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND shop_field = 'S' AND pwht = 'YES'
        """, (iso, page))
        spools = [r[0] for r in cursor.fetchall()]
        conn.close()
        spool_combo['values'] = spools
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        joint_text.delete("1.0", tk.END)

    def refresh_joints(*args):
        iso = iso_var.get().strip()
        spool = spool_var.get().strip()
        if not iso or not spool: return
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT joint_no, rt_asr_date FROM spools
            WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND shop_field = 'S' AND pwht = 'YES'
        """, (iso, spool))
        rows = cursor.fetchall()
        joint_listbox.delete(0, tk.END)
        for joint, rt_asr_date in rows:
            label = f"{joint} (LOCKED)" if rt_asr_date else joint
            joint_listbox.insert(tk.END, label)
            if rt_asr_date:
                joint_listbox.itemconfig(tk.END, {'fg': 'gray'})
        conn.close()
        joint_text.delete("1.0", tk.END)

    def show_joint_info():
        iso = iso_var.get().strip()
        spool = spool_var.get().strip()
        sel = joint_listbox.curselection()
        if not sel: return
        joints = [joint_listbox.get(i).split()[0] for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        output = ""
        for j in joints:
            cursor.execute("""
                SELECT item_1, sch_rating_1, item_2, sch_rating_2, pwht_date, welding_date, rt_asr_report_no
                FROM spools
                WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (iso, spool, j))
            row = cursor.fetchone()
            if row:
                output += (
                    f"Joint {j}:\n"
                    f"  ITEM 1: {row[0]} | SCH/RATING 1: {row[1]}\n"
                    f"  ITEM 2: {row[2]} | SCH/RATING 2: {row[3]}\n"
                    f"  PWHT DATE: {row[4] or '-'} | WELDING DATE: {row[5] or '-'}\n"
                    f"  RT ASR REPORT NO: {row[6] or '-'}\n\n"
                )
        conn.close()
        joint_text.delete("1.0", tk.END)
        joint_text.insert(tk.END, output.strip())

    def update_field(field, value):
        iso = iso_var.get().strip()
        spool = spool_var.get().strip()
        sel = joint_listbox.curselection()
        if not iso or not spool or not sel:
            messagebox.showerror("Error", "Please complete all selections.")
            return
        joints = [joint_listbox.get(i).split()[0] for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        updated = 0
        skipped = []
        for j in joints:
            cursor.execute(f"SELECT {field} FROM spools WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND joint_no = ?", (iso, spool, j))
            if cursor.fetchone()[0]:
                skipped.append(j)
                continue
            cursor.execute(f"""
                UPDATE spools SET {field} = ? WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND joint_no = ?
            """, (value, iso, spool, j))
            updated += 1
        conn.commit()
        conn.close()
        msg = f"{field.replace('_',' ').upper()} updated for {updated} joint(s)."
        if skipped:
            msg += f"\nSkipped: {', '.join(skipped)}"
        messagebox.showinfo("Success", msg)
        refresh_joints()
        show_joint_info()

    # ─── Bindings ───────────────────────────────────────────────────────────
    iso_var.trace_add("write", update_iso_list)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    page_combo.bind("<<ComboboxSelected>>", refresh_spools)
    spool_combo.bind("<<ComboboxSelected>>", refresh_joints)
    joint_listbox.bind("<<ListboxSelect>>", lambda e: show_joint_info())

    for iso in all_iso_list:
        iso_listbox.insert(tk.END, iso)

    return frame
