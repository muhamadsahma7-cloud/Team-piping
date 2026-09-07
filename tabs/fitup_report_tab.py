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

    # ─── ISO Filter Entry ───
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

    # ─── Page & Spool Selection ───
    tk.Label(left_panel, text="PAGE NO:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    page_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    page_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    page_combo.bind("<<ComboboxSelected>>", lambda e: update_spools())

    tk.Label(left_panel, text="DWG SPOOL NO:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    spool_combo = ttk.Combobox(left_panel, width=28, state="readonly")
    spool_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    spool_combo.bind("<<ComboboxSelected>>", lambda e: update_joints())

    # ─── Joint List ───
    tk.Label(left_panel, text="JOINT NO (multiple):").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
    joint_listbox = tk.Listbox(left_panel, width=30, height=6, selectmode=tk.MULTIPLE)
    joint_listbox.grid(row=4, column=1, padx=5, pady=5, sticky="w")
    joint_listbox.bind("<<ListboxSelect>>", lambda e: show_joint_details())

    # ─── Right Panel Display ───
    readonly_text = tk.Text(right_panel, width=60, height=28, bg="#f4f4f4")
    readonly_text.pack(padx=10, pady=10)

    # ─── Data Update Helpers ───
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
            SELECT joint_no, fitup_inspection_date FROM spools
            WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND shop_field = 'S'
        """, (iso, page, spool))
        joints = cursor.fetchall()
        conn.close()
        joint_listbox.delete(0, tk.END)
        for joint_no, date in joints:
            label = f"{joint_no} (LOCKED)" if date else f"{joint_no}"
            joint_listbox.insert(tk.END, label)
            joint_listbox.itemconfig(tk.END, foreground="gray" if date else "black")
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
                SELECT item_1, sch_rating_1, item_2, sch_rating_2, heat_no_1, heat_no_2, fu_report_no, welding_process
                FROM spools
                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (iso, page, spool, j))
            row = cursor.fetchone()
            if row:
                details += (
                    f"Joint {j}:\n"
                    f"  ITEM 1: {row[0]} | SCH 1: {row[1]}\n"
                    f"  ITEM 2: {row[2]} | SCH 2: {row[3]}\n"
                    f"  HEAT NO. 1: {row[4] if row[4] else '-'}\n"
                    f"  HEAT NO. 2: {row[5] if row[5] else '-'}\n"
                    f"  FU REPORT NO: {row[6] if row[6] else '-'}\n"
                    f"  WELDING PROCESS: {row[7] if row[7] else '-'}\n\n"
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
            messagebox.showwarning("Warning", "Please select ISO, PAGE, SPOOL, and JOINT(s).")
            return

        conn = sqlite3.connect("database/spool_tracking.db")
        cursor = conn.cursor()
        updated_count = 0
        for joint in joints:
            cursor.execute(f"""
                UPDATE spools SET {field} = ? 
                WHERE iso_dwg_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (value, iso, page, spool, joint))
            updated_count += 1
        conn.commit()
        conn.close()
        show_joint_details()
        update_joints()
        messagebox.showinfo("Success", f"{field.replace('_', ' ').upper()} updated for {updated_count} joint(s).")

    def create_section(label, field):
        row = create_section.counter
        var = tk.StringVar()

        # Prefill with today date if field is date
        if "date" in field:
            var.set(datetime.today().strftime("%Y-%m-%d"))

        tk.Label(left_panel, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        entry = tk.Entry(left_panel, textvariable=var, width=25)
        entry.grid(row=row, column=1, padx=(5,0), pady=5, sticky="w")
        btn = tk.Button(
            left_panel, text="Save",
            command=lambda: update_field(field, var.get()),
            bg="#1E90FF", fg="white", activebackground="#1C86EE", relief="raised"
        )
        btn.grid(row=row, column=2, padx=(5, 0), pady=5, sticky="w")
        create_section.counter += 1

    create_section.counter = 5
    create_section("FIT UP INSPECTION DATE:", "fitup_inspection_date")
    create_section("HEAT NO. 1:", "heat_no_1")
    create_section("HEAT NO. 2:", "heat_no_2")
    create_section("FU REPORT NO:", "fu_report_no")
    create_section("WELDING PROCESS:", "welding_process")

    return frame
