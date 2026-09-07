import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = ttk.Frame(parent)

    # ─── Preload ISO + Spools ───
    conn = sqlite3.connect("database/spool_tracking.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
    all_iso_list = sorted([row[0] for row in cursor.fetchall()])
    cursor.execute("SELECT DISTINCT iso_dwg_no, dwg_spool_no, iso_run_no FROM spools WHERE shop_field = 'S'")
    iso_spool_triplets = cursor.fetchall()
    conn.close()

    # ─── Style Configuration ───
    style = ttk.Style()
    style.configure("TButton", font=("Segoe UI", 10))
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("TEntry", font=("Segoe UI", 10))
    style.configure("TCombobox", font=("Segoe UI", 10))

    # ─── Panel Layout ───
    left_panel = ttk.Frame(frame)
    left_panel.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

    center_panel = ttk.Frame(frame)
    center_panel.grid(row=0, column=1, padx=10, pady=5, sticky="n")

    right_panel = ttk.Frame(frame)
    right_panel.grid(row=0, column=2, padx=10, pady=5, sticky="n")

    # ─── ISO Entry ───
    tk.Label(left_panel, text="Type ISO DWG NO:").pack(anchor="w")
    iso_var = tk.StringVar()
    tk.Entry(left_panel, textvariable=iso_var, width=30).pack(anchor="w")

    iso_listbox = tk.Listbox(left_panel, height=6, width=30)
    iso_listbox.pack(anchor="w")

    tk.Label(left_panel, text="DWG SPOOL NO:").pack(anchor="w", pady=(10, 0))
    spool_combo = ttk.Combobox(left_panel, width=30, state="readonly")
    spool_combo.pack(anchor="w")

    tk.Label(left_panel, text="JOINT NO(s):").pack(anchor="w", pady=(10, 0))
    joint_listbox = tk.Listbox(left_panel, selectmode=tk.MULTIPLE, width=30, height=10)
    joint_listbox.pack(anchor="w")

    joint_summary_label = tk.Label(left_panel, text="", font=("Segoe UI", 9, "italic"))
    joint_summary_label.pack(anchor="w", pady=3)

    # ─── Detail Fields ───
    today_str = datetime.today().strftime("%Y-%m-%d")
    weld_date_var = tk.StringVar(value=today_str)
    visual_var = tk.StringVar()
    process_var = tk.StringVar()
    root_welder_var = tk.StringVar()
    cap_welder_var = tk.StringVar()
    wps_var = tk.StringVar()

    def create_labeled_entry_with_button(label_text, var, row, save_command):
        tk.Label(center_panel, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        entry = tk.Entry(center_panel, textvariable=var, width=25)
        entry.grid(row=row, column=1, padx=(5, 0), pady=5, sticky="w")
        save_btn = tk.Button(center_panel, text="Save", command=save_command, bg="#1E90FF", fg="white", activebackground="#1C86EE", relief="raised")
        save_btn.grid(row=row, column=2, padx=(5, 0), pady=5, sticky="w")

    create_labeled_entry_with_button("WELDING INSPECTION DATE:", weld_date_var, 0, lambda: update_field("welding_inspection_date", weld_date_var.get()))
    create_labeled_entry_with_button("VISUAL REPORT NO:", visual_var, 1, lambda: update_field("visual_report_no", visual_var.get()))
    create_labeled_entry_with_button("WELDING PROCESS:", process_var, 2, lambda: update_field("welding_process", process_var.get()))
    create_labeled_entry_with_button("ROOT WELDER NO:", root_welder_var, 3, lambda: update_field("root_welder_no", root_welder_var.get()))
    create_labeled_entry_with_button("CAPPING WELDER NO:", cap_welder_var, 4, lambda: update_field("capping_welder_no", cap_welder_var.get()))
    create_labeled_entry_with_button("WPS NO:", wps_var, 5, lambda: update_field("wps_no", wps_var.get()))

    joint_detail_title = tk.Label(right_panel, text="Joint Detail View", font=("Segoe UI", 10, "bold"))
    joint_detail_title.pack(anchor="w")
    joint_detail_text = tk.Text(right_panel, width=50, height=15, bg="#f4f4f4", font=("Segoe UI", 10))
    joint_detail_text.pack()

    def parse_spool_and_page():
        full = spool_combo.get().strip()
        if " (Pg " in full:
            spool = full.split(" (Pg ")[0]
            page = full.split(" (Pg ")[1].rstrip(")")
            return spool, page
        return full, None

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
        selected = iso_listbox.get(sel[0])
        iso_var.set(selected)
        iso_listbox.delete(0, tk.END)
        update_spools()

    def update_spools():
        iso = iso_var.get().strip()
        spools = [(s, p) for i, s, p in iso_spool_triplets if i == iso]
        formatted_spools = [f"{s} (Pg {p})" for s, p in spools]
        spool_combo['values'] = formatted_spools
        spool_combo.set('')
        joint_listbox.delete(0, tk.END)
        joint_detail_text.delete("1.0", tk.END)
        joint_summary_label.config(text="")

    def update_joints(event=None):
        iso = iso_var.get().strip()
        spool, page = parse_spool_and_page()
        if not iso or not spool or not page:
            return

        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT joint_no, fitup_inspection_date, welding_inspection_date, item_1, sch_rating_1, item_2, sch_rating_2, root_welder_no, capping_welder_no, wps_no, visual_report_no, welding_process
            FROM spools
            WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND iso_run_no = ? AND shop_field = 'S'
        """, (iso, spool, page))
        joints_data = cur.fetchall()
        conn.close()

        joint_listbox.delete(0, tk.END)
        joint_detail_text.delete("1.0", tk.END)

        total = locked = no_fit = 0
        for joint, fitup_date, weld_date, item1, sch1, item2, sch2, root, cap, wps, visual, process in joints_data:
            total += 1
            if weld_date:
                joint_listbox.insert(tk.END, f"{joint} (Locked)")
                joint_listbox.itemconfig(tk.END, {'bg': '#d3d3d3'})
                locked += 1
            elif not fitup_date:
                joint_listbox.insert(tk.END, f"{joint} (No Fit-Up)")
                joint_listbox.itemconfig(tk.END, {'fg': 'red'})
                no_fit += 1
            else:
                joint_listbox.insert(tk.END, str(joint))

            joint_detail_text.insert(tk.END, f"Joint {joint}:")
            joint_detail_text.insert(tk.END, f"\nITEM 1: {item1}, SCH 1: {sch1}\nITEM 2: {item2}, SCH 2: {sch2}")
            joint_detail_text.insert(tk.END, f"\nROOT WELDER: {root}\nCAPPING WELDER: {cap}\nWPS: {wps}")
            joint_detail_text.insert(tk.END, f"\nVISUAL REPORT NO: {visual}\nWELDING PROCESS: {process}\n\n")

        joint_summary_label.config(text=f"Total: {total} | Locked: {locked} | No Fit-Up: {no_fit}")

    spool_combo.bind("<<ComboboxSelected>>", update_joints)
    iso_var.trace_add("write", update_iso_list)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)

    for iso in all_iso_list:
        iso_listbox.insert(tk.END, iso)

    def get_selection():
        iso = iso_var.get().strip()
        spool, page = parse_spool_and_page()
        joints = [joint_listbox.get(i).split()[0] for i in joint_listbox.curselection()]
        return iso, spool, page, joints

    def update_field(column, value):
        iso, spool, page, joints = get_selection()
        if not (iso and spool and page and joints):
            messagebox.showwarning("Warning", "Please select ISO, Spool, and Joint(s)")
            return
        if column == "visual_report_no" and not value:
            messagebox.showwarning("Warning", "Visual Report No is required!")
            return

        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()
        blocked = []
        not_fitup = []

        for joint in joints:
            cur.execute("""
                SELECT fitup_inspection_date, welding_inspection_date FROM spools
                WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND iso_run_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (iso, spool, page, joint))
            result = cur.fetchone()
            if not result:
                continue
            fitup_date, weld_date = result

            if column == "welding_inspection_date" and weld_date:
                blocked.append(joint)
                continue
            if not fitup_date:
                not_fitup.append(joint)
                continue

            cur.execute(f"""
                UPDATE spools SET {column} = ?
                WHERE iso_dwg_no = ? AND dwg_spool_no = ? AND iso_run_no = ? AND joint_no = ? AND shop_field = 'S'
            """, (value, iso, spool, page, joint))

        conn.commit()
        conn.close()

        msg = f"Successfully updated {column} for {len(joints) - len(blocked) - len(not_fitup)} joint(s)."
        if blocked:
            msg += f"\nSkipped {len(blocked)} joint(s) with locked Welding Inspection Date."
        if not_fitup:
            msg += f"\nSkipped {len(not_fitup)} joint(s) without Fit-Up."
        messagebox.showinfo("Update Result", msg)
        update_joints()

    return frame