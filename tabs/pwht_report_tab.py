import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = ttk.Frame(parent)

    # ─── Layout ─ Left and Right Panel ─────────────────────────────
    left_panel = ttk.Frame(frame)
    left_panel.grid(row=0, column=0, sticky="nw")
    right_panel = ttk.Frame(frame)
    right_panel.grid(row=0, column=1, padx=20, sticky="ne")

    # ─── Preload ISO Data ──────────────────────────────────────────
    conn = sqlite3.connect("database/spool_tracking.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S' AND rt_bsr_date IS NOT NULL AND pwht = 'YES'")
    all_iso_list = sorted([r[0] for r in cursor.fetchall()])
    cursor.execute("SELECT DISTINCT iso_dwg_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S' AND rt_bsr_date IS NOT NULL AND pwht = 'YES'")
    iso_page_spool = cursor.fetchall()
    conn.close()

    # ─── Left Panel ────────────────────────────────────────────────
    tk.Label(left_panel, text="Type ISO DWG NO:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    iso_var = tk.StringVar()
    tk.Entry(left_panel, textvariable=iso_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

    iso_listbox = tk.Listbox(left_panel, height=6, width=30)
    iso_listbox.grid(row=1, column=0, columnspan=2, padx=5, sticky="w")
    scroll = tk.Scrollbar(left_panel, orient="vertical", command=iso_listbox.yview)
    iso_listbox.configure(yscrollcommand=scroll.set)
    scroll.grid(row=1, column=2, sticky="ns")

    tk.Label(left_panel, text="PAGE NO:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    page_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    page_combo.grid(row=2, column=1, padx=5, sticky="w")

    tk.Label(left_panel, text="DWG SPOOL NO:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    spool_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    spool_combo.grid(row=3, column=1, padx=5, sticky="w")

    tk.Label(left_panel, text="JOINT NO:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
    joint_listbox = tk.Listbox(left_panel, selectmode=tk.MULTIPLE, width=30, height=6)
    joint_listbox.grid(row=4, column=1, padx=5, pady=5, sticky="w")

    # ─── Input Fields ──────────────────────────────────────────────
    today = datetime.today().strftime("%Y-%m-%d")
    pwht_date_var = tk.StringVar(value=today)
    pwht_report_var = tk.StringVar()

    tk.Label(left_panel, text="PWHT DATE:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
    tk.Entry(left_panel, textvariable=pwht_date_var, width=25).grid(row=5, column=1, sticky="w", padx=(5,0))
    tk.Button(left_panel, text="💾", bg="#1976D2", fg="white", width=4,
              command=lambda: update_field("pwht_date", pwht_date_var.get())).grid(row=5, column=2, padx=5)

    tk.Label(left_panel, text="PWHT REPORT NO:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
    tk.Entry(left_panel, textvariable=pwht_report_var, width=25).grid(row=6, column=1, sticky="w", padx=(5,0))
    tk.Button(left_panel, text="💾", bg="#F57C00", fg="white", width=4,
              command=lambda: update_field("pwht_report_no", pwht_report_var.get())).grid(row=6, column=2, padx=5)

    # ─── Readonly Joint Details Panel ─────────────────────────────
    readonly_text = tk.Text(right_panel, width=60, height=28, bg="#f4f4f4")
    readonly_text.pack(padx=10, pady=10)

    # ─── Logic Functions ───────────────────────────────────────────
    def update_iso_list(*args):
        typed = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso_list:
            if typed in iso.lower():
                iso_listbox.insert(tk.END, iso)

    def on_iso_select(event):
        sel = iso_listbox.curselection()
        if not sel:
            return
        iso = iso_listbox.get(sel[0])
        iso_var.set(iso)
        iso_listbox.delete(0, tk.END)
        refresh_pages()

    def refresh_pages():
        iso = iso_var.get().strip()
        pages = sorted(set([row[1] for row in iso_page_spool if row[0] == iso]))
        page_combo['values'] = pages
        page_combo.set('')
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def refresh_spools(event=None):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spools = sorted([row[2] for row in iso_page_spool if row[0] == iso and row[1] == page])
        spool_combo['values'] = spools
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def refresh_joints(event=None):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not iso or not spool or not page:
            return
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT joint_no, pwht_date
            FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ?
              AND shop_field = 'S' AND rt_bsr_date IS NOT NULL AND pwht = 'YES'
        """, (iso, page, spool))
        results = cursor.fetchall()
        conn.close()
        joint_listbox.delete(0, tk.END)
        for joint, pwht_date in results:
            label = f"{joint} (LOCKED)" if pwht_date else str(joint)
            joint_listbox.insert(tk.END, label)
            joint_listbox.itemconfig(tk.END, {'fg': 'gray'} if pwht_date else {'fg': 'black'})
        readonly_text.delete("1.0", tk.END)

    def show_joint_info():
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        sel = joint_listbox.curselection()
        if not sel:
            return
        joints = [joint_listbox.get(i).split()[0] for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        output = ""
        for j in joints:
            cursor.execute("""
                SELECT item_1, sch_rating_1, item_2, sch_rating_2, pwht_report_no
                FROM spools
                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ?
            """, (iso, page, spool, j))
            row = cursor.fetchone()
            if row:
                output += (
                    f"Joint {j}:\n"
                    f"  ITEM 1: {row[0]} | SCH/RATING 1: {row[1]}\n"
                    f"  ITEM 2: {row[2]} | SCH/RATING 2: {row[3]}\n"
                    f"  PWHT REPORT NO: {row[4] if row[4] else '-'}\n\n"
                )
        conn.close()
        readonly_text.delete("1.0", tk.END)
        readonly_text.insert(tk.END, output.strip())

    def update_field(field, value):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        sel = joint_listbox.curselection()
        if not iso or not spool or not sel:
            messagebox.showerror("Error", "Please select ISO, PAGE, Spool, and Joint(s).")
            return
        joints = [joint_listbox.get(i).split()[0] for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        skipped = []
        updated = 0
        for j in joints:
            cursor.execute(f"SELECT {field} FROM spools WHERE iso_dwg_no=? AND iso_run_no=? AND dwg_spool_no=? AND joint_no=?", (iso, page, spool, j))
            current = cursor.fetchone()[0]
            if current:
                skipped.append(str(j))
            else:
                cursor.execute(f"UPDATE spools SET {field} = ? WHERE iso_dwg_no=? AND iso_run_no=? AND dwg_spool_no=? AND joint_no=?",
                               (value, iso, page, spool, j))
                updated += 1
        conn.commit()
        conn.close()
        show_joint_info()
        refresh_joints()
        msg = f"{field.replace('_',' ').upper()} updated for {updated} joint(s)."
        if skipped:
            msg += f"\nSkipped (already filled):\n" + ", ".join(skipped)
        messagebox.showinfo("Success", msg)

    # ─── Events ────────────────────────────────────────────────────
    iso_var.trace_add("write", update_iso_list)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    page_combo.bind("<<ComboboxSelected>>", refresh_spools)
    spool_combo.bind("<<ComboboxSelected>>", refresh_joints)
    joint_listbox.bind("<<ListboxSelect>>", lambda e: show_joint_info())

    for iso in all_iso_list:
        iso_listbox.insert(tk.END, iso)

    return frame
