import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = ttk.Frame(parent)

    # ─── Layout: Left Panel and Right Detail Panel ───
    left_panel = ttk.Frame(frame)
    left_panel.grid(row=0, column=0, sticky="nw")
    right_panel = ttk.Frame(frame)
    right_panel.grid(row=0, column=1, padx=20, sticky="ne")

    # ─── Load ISO & Spools ───
    conn = sqlite3.connect("database/spool_tracking.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
    all_iso_list = sorted([row[0] for row in cursor.fetchall()])
    cursor.execute("SELECT DISTINCT iso_dwg_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S'")
    iso_page_spool = cursor.fetchall()
    conn.close()

    tk.Label(left_panel, text="Type ISO DWG NO:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    iso_var = tk.StringVar()
    iso_entry = tk.Entry(left_panel, textvariable=iso_var, width=30)
    iso_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    iso_listbox = tk.Listbox(left_panel, height=6, width=30)
    iso_listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="we")

    def update_iso_listbox(*args):
        typed = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso_list:
            if typed in iso.lower():
                iso_listbox.insert(tk.END, iso)

    def select_iso_from_list(event):
        selection = iso_listbox.curselection()
        if selection:
            iso = iso_listbox.get(selection[0])
            iso_var.set(iso)
            update_pages()
            iso_listbox.delete(0, tk.END)

    iso_var.trace_add('write', update_iso_listbox)
    iso_listbox.bind("<<ListboxSelect>>", select_iso_from_list)

    tk.Label(left_panel, text="PAGE NO:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    page_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    page_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    page_combo.bind("<<ComboboxSelected>>", lambda e: update_spools())

    tk.Label(left_panel, text="DWG SPOOL NO:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    spool_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    spool_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    spool_combo.bind("<<ComboboxSelected>>", lambda e: update_joints())

    tk.Label(left_panel, text="JOINT NO (multiple):").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
    joint_listbox = tk.Listbox(left_panel, width=30, height=6, selectmode=tk.MULTIPLE)
    joint_listbox.grid(row=4, column=1, padx=5, pady=5, sticky="w")
    joint_listbox.bind("<<ListboxSelect>>", lambda e: show_joint_details())

    today_str = datetime.today().strftime("%Y-%m-%d")
    readonly_text = tk.Text(right_panel, width=60, height=28, bg="#f4f4f4")
    readonly_text.pack(padx=10, pady=10)

    rt_date_var = tk.StringVar(value=today_str)
    rt_report_var = tk.StringVar()

    def update_pages():
        iso = iso_var.get().strip()
        pages = sorted(set([row[1] for row in iso_page_spool if row[0] == iso]))
        page_combo['values'] = pages
        page_combo.set('')
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def update_spools():
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spools = sorted([row[2] for row in iso_page_spool if row[0] == iso and row[1] == page])
        spool_combo['values'] = spools
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        readonly_text.delete("1.0", tk.END)

    def update_joints():
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not iso or not spool or not page:
            return
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT joint_no, rt_bsr_date
            FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ?
            AND shop_field = 'S'
            AND welding_inspection_date IS NOT NULL
            AND (pwht = 'YES' OR pwht = 'NO')
        """, (iso, page, spool))
        results = cursor.fetchall()
        conn.close()

        joint_listbox.delete(0, tk.END)
        for idx, (joint_no, rt_bsr_date) in enumerate(results):
            label = f"{joint_no} (LOCKED)" if rt_bsr_date else str(joint_no)
            joint_listbox.insert(tk.END, label)
            joint_listbox.itemconfig(idx, {'fg': 'gray'} if rt_bsr_date else {'fg': 'black'})
        readonly_text.delete("1.0", tk.END)

    def show_joint_details():
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        sel = joint_listbox.curselection()
        if not sel:
            return
        joints = [joint_listbox.get(i).split()[0] for i in sel]
        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        details = ""
        for j in joints:
            cursor.execute("""
                SELECT item_1, sch_rating_1, item_2, sch_rating_2, rt_bsr_report_no
                FROM spools
                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (iso, page, spool, j))
            row = cursor.fetchone()
            if row:
                details += (
                    f"Joint {j}:\n"
                    f"  ITEM 1: {row[0]} | SCH/RATING 1: {row[1]}\n"
                    f"  ITEM 2: {row[2]} | SCH/RATING 2: {row[3]}\n"
                    f"  RT BSR REPORT NO: {row[4] if row[4] else '-'}\n\n"
                )
        conn.close()
        readonly_text.delete("1.0", tk.END)
        readonly_text.insert(tk.END, details.strip())

    def update_field(field, value):
        iso = iso_var.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        joints = [joint_listbox.get(i).split()[0] for i in joint_listbox.curselection()]

        if not (iso and page and spool and joints):
            messagebox.showerror("Error", "Please select ISO, PAGE, SPOOL, and at least one Joint.")
            return

        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        updated_count = 0
        skipped = []
        for joint in joints:
            cursor.execute(f"SELECT {field} FROM spools WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ?", (iso, page, spool, joint))
            existing = cursor.fetchone()
            if existing and existing[0]:
                skipped.append(joint)
                continue
            cursor.execute(f"UPDATE spools SET {field} = ? WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'", (value, iso, page, spool, joint))
            updated_count += 1
        conn.commit()
        conn.close()
        show_joint_details()
        update_joints()
        msg = f"{field.replace('_', ' ').upper()} updated for {updated_count} joint(s)."
        if skipped:
            msg += f"\nSkipped {len(skipped)} joint(s): {', '.join(skipped)}"
        messagebox.showinfo("Update Result", msg)

    # ─── Input Fields & Save Buttons ───
    row_start = 5
    ttk.Label(left_panel, text="RT BSR DATE:").grid(row=row_start, column=0, padx=5, pady=5, sticky="w")
    entry1 = ttk.Entry(left_panel, textvariable=rt_date_var, width=25)
    entry1.grid(row=row_start, column=1, padx=(5,0), pady=5, sticky="w")
    tk.Button(left_panel, text="Save", width=6, bg="#1976D2", fg="white", command=lambda: update_field("rt_bsr_date", rt_date_var.get())).grid(row=row_start, column=2, padx=5, pady=5)

    ttk.Label(left_panel, text="RT BSR REPORT NO:").grid(row=row_start+1, column=0, padx=5, pady=5, sticky="w")
    entry2 = ttk.Entry(left_panel, textvariable=rt_report_var, width=25)
    entry2.grid(row=row_start+1, column=1, padx=(5,0), pady=5, sticky="w")
    tk.Button(left_panel, text="Save", width=6, bg="#F57C00", fg="white", command=lambda: update_field("rt_bsr_report_no", rt_report_var.get())).grid(row=row_start+1, column=2, padx=5, pady=5)

    return frame
