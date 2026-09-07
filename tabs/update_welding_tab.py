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
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
            all_iso = sorted(row[0] for row in cur.fetchall())
            cur.execute("SELECT iso_dwg_no, line_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S'")
            iso_data = cur.fetchall()
            return all_iso, iso_data
    
    all_iso, iso_data = load_data()

    # ─── Widgets ───
    tk.Label(frame, text="Type ISO DWG NO", font=("Arial", 12, "bold")).pack(anchor="w")
    iso_var = tk.StringVar()
    iso_entry = tk.Entry(frame, textvariable=iso_var, width=50, font=("Arial", 11))
    iso_entry.pack(anchor="w", pady=5)

    iso_listbox = tk.Listbox(frame, height=8, width=50, font=("Arial", 10))
    iso_listbox.pack(anchor="w", pady=(0,8))
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=iso_listbox.yview)
    iso_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.place(in_=iso_listbox, relx=1.0, relheight=1.0, anchor="ne")

    tk.Label(frame, text="LINE NO", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,0))
    line_combo = ttk.Combobox(frame, width=50, font=("Arial", 11))
    line_combo.pack(anchor="w", pady=5)

    tk.Label(frame, text="PAGE NO", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,0))
    page_combo = ttk.Combobox(frame, width=50, font=("Arial", 11))
    page_combo.pack(anchor="w", pady=5)

    tk.Label(frame, text="DWG SPOOL NO", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,0))
    spool_combo = ttk.Combobox(frame, width=50, font=("Arial", 11))
    spool_combo.pack(anchor="w", pady=5)

    tk.Label(frame, text="JOINT NO(s)", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,0))
    joint_listbox = tk.Listbox(frame, height=8, selectmode="multiple", width=50, font=("Arial", 10))
    joint_listbox.pack(anchor="w", pady=5)

    tk.Label(frame, text="Joint Info", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,0))
    info_text = tk.Text(frame, height=6, width=60, state="disabled", font=("Courier", 11), fg="blue")
    info_text.pack(anchor="w", pady=5)

    # Welding Date + Save button side by side - bigger layout
    date_frame = tk.Frame(frame)
    date_frame.pack(anchor="w", pady=(15, 8))

    tk.Label(date_frame, text="Welding Date (dd/mm/yyyy):", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
    weld_entry = tk.Entry(date_frame, width=25, font=("Arial", 11))
    weld_entry.grid(row=0, column=1, padx=10)
    weld_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

    def refresh_data():
        """Refresh all data from database and reset form"""
        try:
            # Reload data from database
            nonlocal all_iso, iso_data
            all_iso, iso_data = load_data()
            
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
            
            # Clear info panel
            info_text.config(state="normal")
            info_text.delete(1.0, tk.END)
            info_text.config(state="disabled")
            
            # Reset date to today
            today_str = datetime.today().strftime("%d/%m/%Y")
            weld_entry.config(state="normal")
            weld_entry.delete(0, tk.END)
            weld_entry.insert(0, today_str)
            
            messagebox.showinfo("Success", "Data refreshed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")

    def update_weld_date():
        if weld_entry.cget("state") in ("readonly", "disabled"):
            messagebox.showinfo("Info", "Cannot update this welding date.")
            return

        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        date_str = weld_entry.get().strip()
        sel = joint_listbox.curselection()
        if not (iso and line and page and spool and date_str and sel):
            messagebox.showerror("Error", "Please complete all fields.")
            return
        try:
            weld_date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format.")
            return

        joint_nos = [joint_listbox.get(i).split()[0] for i in sel if "(Locked)" not in joint_listbox.get(i)]
        if not joint_nos:
            messagebox.showinfo("Info", "No editable joints selected.")
            return

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            for joint in joint_nos:
                cur.execute("""
                    UPDATE spools SET welding_date=? 
                    WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=? AND joint_no=?
                """, (weld_date, iso, line, page, spool, joint))
            conn.commit()

        messagebox.showinfo("Success", f"Welding Date updated for {len(joint_nos)} joint(s).")
        update_joint_list(None)

    save_button = tk.Button(date_frame, text="✅ Save", command=update_weld_date, width=12, 
                           font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", pady=8)
    save_button.grid(row=0, column=2, padx=10)
    
    refresh_button = tk.Button(date_frame, text="🔄 Refresh", command=refresh_data, width=12, 
                              font=("Arial", 12, "bold"), bg="#2196F3", fg="white", pady=8)
    refresh_button.grid(row=0, column=3, padx=10)

    # ─── Functions ───
    def update_iso_listbox(*args):
        keyword = iso_var.get().strip().lower()
        iso_listbox.delete(0, tk.END)
        for iso in all_iso:
            if keyword in iso.lower():
                iso_listbox.insert(tk.END, iso)

    def on_iso_select(event):
        sel = iso_listbox.curselection()
        if not sel: return
        iso = iso_listbox.get(sel[0])
        iso_var.set(iso)
        iso_listbox.delete(0, tk.END)
        lines = sorted(set(r[1] for r in iso_data if r[0] == iso))
        line_combo['values'] = lines
        line_combo.set("")
        page_combo.set("")
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)
        info_text.config(state="normal")
        info_text.delete(1.0, tk.END)
        info_text.config(state="disabled")
        weld_entry.config(state="normal")
        weld_entry.delete(0, tk.END)
        weld_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

    def on_line_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        pages = sorted(set(r[2] for r in iso_data if r[0] == iso and r[1] == line))
        page_combo['values'] = pages
        page_combo.set("")
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)

    def on_page_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spools = sorted(set(r[3] for r in iso_data if r[0] == iso and r[1] == line and r[2] == page))
        spool_combo['values'] = spools
        spool_combo.set("")
        joint_listbox.delete(0, tk.END)

    def update_joint_list(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not (iso and line and page and spool): return
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT joint_no, fitup_date, welding_date, item_1, sch_rating_1, item_2, sch_rating_2
                FROM spools
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=? AND shop_field='S'
            """, (iso, line, page, spool))
            results = cur.fetchall()

        joint_listbox.delete(0, tk.END)
        for r in results:
            joint, fitup, weld, *_ = r
            label = joint
            if not fitup:
                label += " (No Fit-Up)"
            elif weld:
                label += " (Locked)"
            joint_listbox.insert(tk.END, label)

    def show_joint_info(event):
        sel = joint_listbox.curselection()
        if not sel: return
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        joint = joint_listbox.get(sel[0]).split()[0]

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT joint_size, item_1, sch_rating_1, item_2, sch_rating_2, fitup_date, welding_date
                FROM spools
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=? AND joint_no=?
            """, (iso, line, page, spool, joint))
            r = cur.fetchone()

        if not r: return
        joint_size, item1, sch1, item2, sch2, fitup, weld = r
        info_text.config(state="normal")
        info_text.delete(1.0, tk.END)
        info_text.insert(tk.END, (
            f"JOINT SIZE : {joint_size}\n"
            f"ITEM 1     : {item1}\n"
            f"SCH/RATE 1: {sch1}\n"
            f"ITEM 2     : {item2}\n"
            f"SCH/RATE 2: {sch2}"
        ))
        info_text.config(state="disabled")

        weld_entry.config(state="normal")
        weld_entry.delete(0, tk.END)
        if not fitup:
            weld_entry.insert(0, "Fit-Up required")
            weld_entry.config(state="disabled")
        elif weld:
            try:
                weld_disp = datetime.strptime(weld, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                weld_disp = weld
            weld_entry.insert(0, weld_disp)
            weld_entry.config(state="readonly")
        else:
            weld_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

    # ─── Bindings ───
    iso_var.trace_add("write", update_iso_listbox)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    line_combo.bind("<<ComboboxSelected>>", on_line_select)
    page_combo.bind("<<ComboboxSelected>>", on_page_select)
    spool_combo.bind("<<ComboboxSelected>>", update_joint_list)
    joint_listbox.bind("<<ListboxSelect>>", show_joint_info)

    return main_frame