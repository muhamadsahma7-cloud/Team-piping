import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import calendar
from ui_theme import UITheme

def build_tab(parent, permissions):
    """Build the manpower report tab"""
    frame = UITheme.create_styled_frame(parent)
    
    # Check if user has permission to access manpower reports
    if not (permissions.get("manpower") or permissions.get("admin") or permissions.get("all")):
        return build_access_denied_tab(frame)
    
    return build_manpower_content(frame, permissions)

def build_access_denied_tab(frame):
    """Build access denied tab for unauthorized users"""
    # Main container
    main_container = UITheme.create_styled_frame(frame)
    main_container.pack(fill="both", expand=True, padx=UITheme.MAIN_PADDING, pady=UITheme.MAIN_PADDING)
    
    # Header
    header_frame = UITheme.create_styled_frame(main_container)
    header_frame.pack(fill="x", pady=(0, 30))
    
    title_label = UITheme.create_title_label(header_frame, "Access Denied")
    title_label.pack(anchor="w")
    
    subtitle_label = UITheme.create_body_label(header_frame, "You don't have permission to access Manpower Reports")
    subtitle_label.pack(anchor="w", pady=(5, 0))
    
    # Access denied message
    message_frame = UITheme.create_section_frame(main_container, "Permission Required")
    message_frame.pack(fill="x", pady=(0, 20))
    
    message_container = UITheme.create_styled_frame(message_frame)
    message_container.pack(fill="x", padx=20, pady=15)
    
    # Icon and message
    icon_label = tk.Label(message_container, text="🔒", font=("Segoe UI", 48), 
                         fg=UITheme.DANGER_COLOR, bg=UITheme.WHITE_COLOR)
    icon_label.pack(pady=(10, 20))
    
    message_text = UITheme.create_body_label(message_container, 
        "This tab requires 'Manpower Report' permissions.\n\nPlease contact your system administrator to request access.")
    message_text.pack(pady=(0, 20))
    
    # Additional info
    info_frame = UITheme.create_styled_frame(message_container)
    info_frame.pack(fill="x", pady=(20, 0))
    
    info_label = UITheme.create_body_label(info_frame, 
        "Required permissions: Manpower Report, Admin, or All Access")
    info_label.pack()
    
    return frame

def build_manpower_content(frame, permissions):
    """Build the actual manpower report content"""
    
    # Create scrollable container optimized for small monitors
    canvas = tk.Canvas(frame, bg=UITheme.WHITE_COLOR, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = UITheme.create_styled_frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Enable mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
    
    canvas.bind('<Enter>', _bind_to_mousewheel)
    canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Main container
    main_container = UITheme.create_styled_frame(scrollable_frame)
    main_container.pack(fill="both", expand=True, padx=UITheme.MAIN_PADDING, pady=UITheme.MAIN_PADDING)
    
    # Header
    header_frame = UITheme.create_styled_frame(main_container)
    header_frame.pack(fill="x", pady=(0, 30))
    
    title_label = UITheme.create_title_label(header_frame, "Manpower Report")
    title_label.pack(anchor="w")
    
    subtitle_label = UITheme.create_body_label(header_frame, "Track daily manpower allocation for welders and fitters")
    subtitle_label.pack(anchor="w", pady=(5, 0))
    
    # Input section
    input_frame = UITheme.create_section_frame(main_container, "Add Manpower Data")
    input_frame.pack(fill="x", pady=(0, 20))
    
    # Create input form
    form_frame = UITheme.create_styled_frame(input_frame)
    form_frame.pack(fill="x", padx=20, pady=15)
    
    # Date input with dropdown selectors
    date_frame = UITheme.create_styled_frame(form_frame)
    date_frame.pack(fill="x", pady=5)
    
    date_label = UITheme.create_body_label(date_frame, "Date:")
    date_label.pack(side="left", padx=(0, 10))
    
    # Create date dropdown frame
    date_dropdown_frame = UITheme.create_styled_frame(date_frame)
    date_dropdown_frame.pack(side="left")
    
    # Get current date
    now = datetime.now()
    
    # Year dropdown
    year_var = tk.StringVar(value=str(now.year))
    year_combo = ttk.Combobox(date_dropdown_frame, textvariable=year_var, width=6, state="readonly")
    year_combo['values'] = [str(year) for year in range(now.year - 5, now.year + 6)]
    year_combo.pack(side="left", padx=(0, 2))
    
    # Month dropdown
    month_var = tk.StringVar(value=f"{now.month:02d}")
    month_combo = ttk.Combobox(date_dropdown_frame, textvariable=month_var, width=4, state="readonly")
    month_combo['values'] = [f"{month:02d}" for month in range(1, 13)]
    month_combo.pack(side="left", padx=(0, 2))
    
    # Day dropdown
    day_var = tk.StringVar(value=f"{now.day:02d}")
    day_combo = ttk.Combobox(date_dropdown_frame, textvariable=day_var, width=4, state="readonly")
    
    def update_days(*args):
        """Update day dropdown based on selected year and month"""
        try:
            year = int(year_var.get())
            month = int(month_var.get())
            days_in_month = calendar.monthrange(year, month)[1]
            day_combo['values'] = [f"{day:02d}" for day in range(1, days_in_month + 1)]
            
            # Ensure current day selection is valid
            current_day = int(day_var.get())
            if current_day > days_in_month:
                day_var.set(f"{days_in_month:02d}")
        except:
            day_combo['values'] = [f"{day:02d}" for day in range(1, 32)]
    
    # Bind year and month changes to update days
    year_var.trace('w', update_days)
    month_var.trace('w', update_days)
    
    # Initialize days
    update_days()
    day_combo.pack(side="left")
    
    # Format labels
    tk.Label(date_dropdown_frame, text="YYYY").pack(side="left", padx=(5, 0))
    tk.Label(date_dropdown_frame, text="MM").pack(side="left", padx=(15, 0))
    tk.Label(date_dropdown_frame, text="DD").pack(side="left", padx=(15, 0))
    
    # Function to get formatted date string
    def get_date_string():
        return f"{year_var.get()}-{month_var.get()}-{day_var.get()}"
    
    # Function to set date from date object
    def set_date_picker(date_obj):
        year_var.set(str(date_obj.year))
        month_var.set(f"{date_obj.month:02d}")
        day_var.set(f"{date_obj.day:02d}")
        update_days()
    
    # Function to set date from string
    def set_date_var(date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            set_date_picker(date_obj)
        except:
            pass
    
    # Total welders input
    welder_frame = UITheme.create_styled_frame(form_frame)
    welder_frame.pack(fill="x", pady=5)
    
    welder_label = UITheme.create_body_label(welder_frame, "Total Welders:")
    welder_label.pack(side="left", padx=(0, 10))
    
    welder_var = tk.StringVar()
    welder_entry = UITheme.create_styled_entry(welder_frame, textvariable=welder_var, width=10)
    welder_entry.pack(side="left")
    
    # Total fitters input
    fitter_frame = UITheme.create_styled_frame(form_frame)
    fitter_frame.pack(fill="x", pady=5)
    
    fitter_label = UITheme.create_body_label(fitter_frame, "Total Fitters:")
    fitter_label.pack(side="left", padx=(0, 10))
    
    fitter_var = tk.StringVar()
    fitter_entry = UITheme.create_styled_entry(fitter_frame, textvariable=fitter_var, width=10)
    fitter_entry.pack(side="left")
    
    # Buttons frame
    buttons_frame = UITheme.create_styled_frame(form_frame)
    buttons_frame.pack(fill="x", pady=15)
    
    def save_manpower_data():
        """Save manpower data to database"""
        try:
            date = get_date_string()
            welders = welder_var.get().strip()
            fitters = fitter_var.get().strip()
            
            if not date or not welders or not fitters:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format")
                return
            
            # Validate numbers
            try:
                welders_int = int(welders)
                fitters_int = int(fitters)
                if welders_int < 0 or fitters_int < 0:
                    raise ValueError("Numbers must be non-negative")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for welders and fitters")
                return
            
            # Save to database
            with sqlite3.connect("database/spool_tracking.db") as conn:
                cursor = conn.cursor()
                
                # Create table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS manpower_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT UNIQUE,
                        total_welders INTEGER,
                        total_fitters INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert or update record
                cursor.execute('''
                    INSERT OR REPLACE INTO manpower_reports (date, total_welders, total_fitters)
                    VALUES (?, ?, ?)
                ''', (date, welders_int, fitters_int))
                
                conn.commit()
            
            messagebox.showinfo("Success", "Manpower data saved successfully!")
            
            # Clear form
            welder_var.set("")
            fitter_var.set("")
            set_date_picker(datetime.now().date())
            
            # Refresh the data display
            refresh_manpower_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def clear_form():
        """Clear the input form"""
        welder_var.set("")
        fitter_var.set("")
        set_date_picker(datetime.now().date())
    
    # Add buttons
    save_btn = UITheme.create_primary_button(buttons_frame, "Save Data", save_manpower_data)
    save_btn.pack(side="left", padx=(0, 10))
    
    clear_btn = UITheme.create_secondary_button(buttons_frame, "Clear Form", clear_form)
    clear_btn.pack(side="left")
    
    # Data display section
    display_frame = UITheme.create_section_frame(main_container, "Manpower Records")
    display_frame.pack(fill="both", expand=True)
    
    # Create treeview for displaying data (optimized height for small monitors)
    columns = ("Date", "Welders", "Fitters", "Total")
    tree = UITheme.create_styled_treeview(display_frame, columns, height=10)
    tree.pack(fill="both", expand=True, padx=20, pady=15)
    
    # Configure columns
    tree.heading("Date", text="Date")
    tree.heading("Welders", text="Total Welders")
    tree.heading("Fitters", text="Total Fitters")
    tree.heading("Total", text="Total Manpower")
    
    tree.column("Date", width=120, anchor="center")
    tree.column("Welders", width=120, anchor="center")
    tree.column("Fitters", width=120, anchor="center")
    tree.column("Total", width=120, anchor="center")
    
    # Add scrollbar for treeview
    tree_scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scrollbar.set)
    tree_scrollbar.pack(side="right", fill="y")
    
    def refresh_manpower_display():
        """Refresh the manpower data display"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Load data from database
            with sqlite3.connect("database/spool_tracking.db") as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='manpower_reports'
                ''')
                
                if cursor.fetchone():
                    cursor.execute('''
                        SELECT date, total_welders, total_fitters 
                        FROM manpower_reports 
                        ORDER BY date DESC
                    ''')
                    
                    records = cursor.fetchall()
                    
                    for record in records:
                        date, welders, fitters = record
                        total = welders + fitters
                        tree.insert("", "end", values=(date, welders, fitters, total))
                
        except Exception as e:
            print(f"Error loading manpower data: {e}")
    
    def delete_selected():
        """Delete selected manpower record"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a record to delete")
            return
        
        item = tree.item(selected_item[0])
        date = item['values'][0]
        
        result = messagebox.askyesno("Confirm Delete", f"Delete manpower record for {date}?")
        if result:
            try:
                with sqlite3.connect("database/spool_tracking.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM manpower_reports WHERE date = ?", (date,))
                    conn.commit()
                
                messagebox.showinfo("Success", "Record deleted successfully!")
                refresh_manpower_display()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete record: {str(e)}")
    
    # Action buttons for data management
    action_frame = UITheme.create_styled_frame(display_frame)
    action_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    delete_btn = UITheme.create_danger_button(action_frame, "Delete Selected", delete_selected)
    delete_btn.pack(side="left", padx=(0, 10))
    
    refresh_btn = UITheme.create_secondary_button(action_frame, "Refresh Data", refresh_manpower_display)
    refresh_btn.pack(side="left")
    
    # Load initial data
    refresh_manpower_display()
    
    return frame