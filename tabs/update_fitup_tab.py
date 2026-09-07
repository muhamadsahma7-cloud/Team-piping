import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    # Create main container frame
    main_frame = tk.Frame(parent)
    main_frame.pack(fill="both", expand=True)
    
    # Create canvas and scrollbar for entire content
    canvas = tk.Canvas(main_frame)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    frame = tk.Frame(canvas, padx=20, pady=20)
    
    # Configure scrolling
    frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Add mouse wheel support
    def _on_mousewheel(event):
        # Handle both Windows and Linux mouse wheel events
        if event.delta:
            # Windows
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            # Linux
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
    
    # Bind mouse wheel events for both platforms
    canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
    canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
    canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down
    
    # Also bind to the main frame for better coverage
    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
    
    # Bind when entering and unbind when leaving to avoid conflicts
    main_frame.bind('<Enter>', _bind_to_mousewheel)
    main_frame.bind('<Leave>', _unbind_from_mousewheel)

    # ─── Load Data ───
    def load_data():
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
            all_iso_list = sorted([row[0] for row in cursor.fetchall()])
            cursor.execute("SELECT DISTINCT iso_dwg_no, line_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S'")
            iso_line_page_spool = cursor.fetchall()
            return all_iso_list, iso_line_page_spool
    
    all_iso_list, iso_line_page_spool = load_data()

    # ─── Widgets ───
    tk.Label(frame, text="Type ISO DWG NO:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
    iso_var = tk.StringVar()
    iso_entry = tk.Entry(frame, textvariable=iso_var, width=35, font=("Arial", 11))
    iso_entry.grid(row=0, column=1, padx=10, pady=8, sticky="w")

    iso_listbox = tk.Listbox(frame, height=8, width=40, font=("Arial", 10))
    iso_listbox.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="we")
    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=iso_listbox.yview)
    iso_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=1, column=2, sticky="ns", pady=(0, 8))

    tk.Label(frame, text="LINE NO:", font=("Arial", 12, "bold")).grid(row=2, column=0, padx=10, pady=8, sticky="w")
    line_combo = ttk.Combobox(frame, width=35, font=("Arial", 11))
    line_combo.grid(row=2, column=1, padx=10, pady=8, sticky="w")

    tk.Label(frame, text="PAGE NO:", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=10, pady=8, sticky="w")
    page_combo = ttk.Combobox(frame, width=35, font=("Arial", 11))
    page_combo.grid(row=3, column=1, padx=10, pady=8, sticky="w")

    tk.Label(frame, text="DWG SPOOL NO:", font=("Arial", 12, "bold")).grid(row=4, column=0, padx=10, pady=8, sticky="w")
    spool_combo = ttk.Combobox(frame, width=35, font=("Arial", 11))
    spool_combo.grid(row=4, column=1, padx=10, pady=8, sticky="w")

    tk.Label(frame, text="JOINT NO(s):", font=("Arial", 12, "bold")).grid(row=5, column=0, padx=10, pady=8, sticky="nw")
    joint_listbox = tk.Listbox(frame, selectmode="multiple", height=8, width=40, font=("Arial", 10))
    joint_listbox.grid(row=5, column=1, padx=10, pady=8, sticky="w")

    locked_label = tk.Label(frame, text="", fg="gray", justify="left", anchor="w", font=("Courier", 10))
    locked_label.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

    # Joint Info Panel - right side
    info_frame = tk.LabelFrame(frame, text="Joint Info", padx=15, pady=10, font=("Arial", 12, "bold"))
    info_frame.grid(row=0, column=3, rowspan=7, padx=15, pady=10, sticky="nsew")
    joint_info_text = tk.Text(info_frame, height=12, width=50, state="disabled", font=("Courier", 11))
    joint_info_text.pack()

    # Pre-fill today's date
    today_str = datetime.today().strftime("%d/%m/%Y")
    tk.Label(frame, text="Fit-Up Date (dd/mm/yyyy):", font=("Arial", 12, "bold")).grid(row=7, column=0, padx=10, pady=8, sticky="w")
    fitup_entry = tk.Entry(frame, width=35, font=("Arial", 11))
    fitup_entry.insert(0, today_str)
    fitup_entry.grid(row=7, column=1, padx=10, pady=8, sticky="w")

    def update_iso_listbox(*args):
        typed = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso_list:
            if typed in str(iso).lower():
                iso_listbox.insert(tk.END, iso)

    def on_iso_select(event):
        sel = iso_listbox.curselection()
        if not sel: return
        chosen_iso = iso_listbox.get(sel[0])
        iso_var.set(chosen_iso)
        lines = sorted(set([row[1] for row in iso_line_page_spool if row[0] == chosen_iso]))
        line_combo['values'] = lines
        line_combo.set("")
        page_combo.set("")
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)
        iso_listbox.delete(0, tk.END)
        locked_label.config(text="")
        joint_info_text.config(state="normal")
        joint_info_text.delete(1.0, tk.END)
        joint_info_text.config(state="disabled")

    def on_line_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        pages = sorted(set([row[2] for row in iso_line_page_spool if row[0] == iso and row[1] == line]))
        page_combo['values'] = pages
        page_combo.set("")
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)
        locked_label.config(text="")
        joint_info_text.config(state="normal")
        joint_info_text.delete(1.0, tk.END)
        joint_info_text.config(state="disabled")

    def on_page_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spools = sorted(set([row[3] for row in iso_line_page_spool if row[0] == iso and row[1] == line and str(row[2]) == page]))
        spool_combo['values'] = spools
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)
        locked_label.config(text="")
        joint_info_text.config(state="normal")
        joint_info_text.delete(1.0, tk.END)
        joint_info_text.config(state="disabled")

    def update_joints(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not iso or not line or not page or not spool: return
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""SELECT joint_no, fitup_date FROM spools
                           WHERE iso_dwg_no = ? AND line_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND shop_field = 'S'""",
                        (iso, line, page, spool))
            results = cur.fetchall()
        joint_listbox.delete(0, tk.END)
        locked_joints = []
        for joint, fitup in results:
            label = f"{joint} {'(Locked)' if fitup else ''}"
            joint_listbox.insert(tk.END, label)
            if fitup:
                joint_listbox.itemconfig(tk.END, {'fg': 'gray'})
                locked_joints.append(joint)
        locked_label.config(text=f"Locked joints: {', '.join(locked_joints)}" if locked_joints else "")
        fitup_entry.config(state="normal")
        fitup_entry.delete(0, tk.END)
        fitup_entry.insert(0, today_str)
        joint_info_text.config(state="normal")
        joint_info_text.delete(1.0, tk.END)
        joint_info_text.config(state="disabled")

    def show_joint_info(joint_no):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not (iso and line and page and spool and joint_no):
            return
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""SELECT joint_no, joint_size, item_1, sch_rating_1, heat_no_1,
                                  item_2, sch_rating_2, heat_no_2
                           FROM spools
                           WHERE iso_dwg_no = ? AND line_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ?""",
                        (iso, line, page, spool, joint_no))
            result = cur.fetchone()

        if result:
            info_text = (
                f"Joint No     : {result[0]}\n"
                f"Joint Size   : {result[1]}\n"
                f"Item 1       : {result[2]}\n"
                f"Sch/Rating 1 : {result[3]}\n"
                f"Heat No. 1   : {result[4]}\n"
                f"Item 2       : {result[5]}\n"
                f"Sch/Rating 2 : {result[6]}\n"
                f"Heat No. 2   : {result[7]}"
            )
        else:
            info_text = "No joint info found."

        joint_info_text.config(state="normal")
        joint_info_text.delete(1.0, tk.END)
        joint_info_text.insert(tk.END, info_text)
        joint_info_text.config(state="disabled")

    def on_joint_select(event):
        selected = joint_listbox.curselection()
        if selected:
            joint_label = joint_listbox.get(selected[0])
            joint_no = joint_label.split()[0]
            show_joint_info(joint_no)

    def refresh_data():
        """Refresh all data from database and reset form"""
        try:
            # Reload data from database
            nonlocal all_iso_list, iso_line_page_spool
            all_iso_list, iso_line_page_spool = load_data()
            
            # Clear all form fields
            iso_var.set("")
            iso_listbox.delete(0, tk.END)
            line_combo['values'] = []
            line_combo.set("")
            page_combo['values'] = []
            page_combo.set("")
            spool_combo['values'] = []
            spool_combo.set("")
            joint_listbox.delete(0, tk.END)
            locked_label.config(text="")
            
            # Clear joint info panel
            joint_info_text.config(state="normal")
            joint_info_text.delete(1.0, tk.END)
            joint_info_text.config(state="disabled")
            
            # Reset date to today
            today_str = datetime.today().strftime("%d/%m/%Y")
            fitup_entry.delete(0, tk.END)
            fitup_entry.insert(0, today_str)
            
            messagebox.showinfo("Success", "Data refreshed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")

    def update_fitup_date():
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        date = fitup_entry.get().strip()
        selected_indices = joint_listbox.curselection()
        if not iso or not line or not page or not spool or not date or not selected_indices:
            messagebox.showerror("Error", "Please fill all fields and select joints.")
            return
        try:
            formatted_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date format must be dd/mm/yyyy.")
            return
        joint_nos = []
        for i in selected_indices:
            text = joint_listbox.get(i)
            if "(Locked)" not in text:
                joint_nos.append(text.split()[0])
        if not joint_nos:
            messagebox.showinfo("Info", "All selected joints are already locked.")
            return
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            for joint in joint_nos:
                cur.execute("""UPDATE spools SET fitup_date = ?
                               WHERE iso_dwg_no = ? AND line_no = ? AND iso_run_no = ? AND dwg_spool_no = ? AND joint_no = ?""",
                            (formatted_date, iso, line, page, spool, joint))
            conn.commit()
        messagebox.showinfo("Success", f"Fit-Up Date updated for {len(joint_nos)} joints.")
        update_joints(None)

    # ─── Bindings ───
    iso_var.trace_add('write', update_iso_listbox)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    line_combo.bind("<<ComboboxSelected>>", on_line_select)
    page_combo.bind("<<ComboboxSelected>>", on_page_select)
    spool_combo.bind("<<ComboboxSelected>>", update_joints)
    joint_listbox.bind("<<ListboxSelect>>", on_joint_select)

    # Button frame to hold both buttons
    button_frame = tk.Frame(frame)
    button_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=20)
    
    tk.Button(button_frame, text="✅ Update Fit-Up Date", command=update_fitup_date, width=25, 
             font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", pady=8).grid(
        row=0, column=0, padx=(0, 10)
    )
    
    tk.Button(button_frame, text="🔄 Refresh", command=refresh_data, width=15, 
             font=("Arial", 12, "bold"), bg="#2196F3", fg="white", pady=8).grid(
        row=0, column=1, padx=(10, 0)
    )

    return main_frame