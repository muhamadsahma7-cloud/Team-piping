import sqlite3
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import pytz
from ui_theme import UITheme

def build_tab(parent, permissions):
    """Build the enhanced dashboard tab"""
    frame = UITheme.create_styled_frame(parent)
    
    # Store references for refresh functionality
    frame.dashboard_refs = {}
    
    # Create scrollable container that fills the entire window
    canvas = tk.Canvas(frame, bg=UITheme.WHITE_COLOR)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = UITheme.create_styled_frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Add mouse wheel scrolling support
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Bind mouse wheel events
    canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Main container that adapts to window size
    main_container = UITheme.create_styled_frame(scrollable_frame)
    main_container.pack(fill="both", expand=True, padx=UITheme.MAIN_PADDING, pady=UITheme.MAIN_PADDING)
    
    # Update canvas scroll region when content changes
    def update_scroll_region():
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    # Schedule scroll region update
    scrollable_frame.after(1, update_scroll_region)
    
    # Welcome header
    header_frame = UITheme.create_styled_frame(main_container)
    header_frame.pack(fill="x", pady=(0, 30))
    
    welcome_label = UITheme.create_title_label(header_frame, "Project Dashboard")
    welcome_label.pack(anchor="w")
    
    subtitle_label = UITheme.create_body_label(header_frame, "Overview of your piping project status and recent activities")
    subtitle_label.pack(anchor="w", pady=(5, 0))
    
    # Stats cards container with increased spacing
    stats_container = UITheme.create_styled_frame(main_container)
    stats_container.pack(fill="x", pady=(0, 30))
    
    # Get real statistics from database
    stats_data = get_project_statistics()
    
    # Create stats cards in a responsive grid layout
    for i, stat in enumerate(stats_data):
        row = i // 3  # 0 for first row, 1 for second row, etc.
        col = i % 3   # 0, 1, 2 for columns
        
        card = create_stat_card(stats_container, stat["title"], stat["value"], stat["color"])
        card.grid(row=row, column=col, padx=15, pady=10, sticky="ew")
    
    # Configure grid weights for responsive layout (3 columns)
    for i in range(3):
        stats_container.grid_columnconfigure(i, weight=1, minsize=200)
    
    # Configure row weights - now we have 15 stats (5 rows)
    for i in range((len(stats_data) + 2) // 3):  # Calculate number of rows needed
        stats_container.grid_rowconfigure(i, weight=1)
    
    # Content container for activities and quick actions - responsive
    content_container = UITheme.create_styled_frame(main_container)
    content_container.pack(fill="both", expand=True)
    
    # Recent activities panel - responsive width
    activities_frame = UITheme.create_section_frame(content_container, "Recent Activities")
    activities_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
    activities_tree = create_activities_tree(activities_frame)
    activities_tree.pack(fill="both", expand=True, pady=8)
    
    # Store references for refresh
    frame.dashboard_refs['activities_tree'] = activities_tree
    frame.dashboard_refs['stats_container'] = stats_container
    frame.dashboard_refs['permissions'] = permissions
    
    # Populate recent activities
    populate_recent_activities(activities_tree)
    
    # Quick actions panel - responsive but constrained width
    actions_frame = UITheme.create_section_frame(content_container, "Quick Actions")
    actions_frame.pack(side="right", fill="y", padx=(10, 0))
    
    # Set reasonable fixed width for actions
    actions_frame.configure(width=220)
    
    # Quick action buttons based on permissions
    create_quick_actions(actions_frame, permissions, frame)
    
    # Progress visualization panel
    progress_frame = UITheme.create_section_frame(main_container, "Project Progress Overview")
    progress_frame.pack(fill="x", pady=(30, 15))
    
    create_progress_visualization(progress_frame)
    
    # System status panel at bottom
    status_frame = UITheme.create_section_frame(main_container, "System Status")
    status_frame.pack(fill="x", pady=(15, 0))
    
    create_system_status(status_frame)
    
    # Update scroll region after all content is loaded
    main_container.after(100, update_scroll_region)
    
    return frame

def get_project_statistics():
    """Get comprehensive piping project statistics from the database based on joint_size sums"""
    try:
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cursor = conn.cursor()
            
            # Total shop joints - sum of joint_size where shop_field = 'S'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S'")
            shop_joints = cursor.fetchone()[0]
            
            # Total field joints - sum of joint_size where shop_field = 'F'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'F'")
            field_joints = cursor.fetchone()[0]
            
            # Number of work orders
            cursor.execute("SELECT COUNT(DISTINCT wo_no) FROM spools WHERE wo_no IS NOT NULL AND wo_no != ''")
            work_orders = cursor.fetchone()[0]
            
            # Total fit-up completed - sum of joint_size where shop_field = 'S' AND fitup_date exists
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND fitup_date IS NOT NULL AND fitup_date != ''")
            fitup_completed = cursor.fetchone()[0]
            
            # Total welding completed - sum of joint_size where shop_field = 'S' AND welding_date exists
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND welding_date IS NOT NULL AND welding_date != ''")
            welding_completed = cursor.fetchone()[0]
            
            # Calculate progress percentage: total welding done / total shop joints * 100
            progress_percentage = (welding_completed / shop_joints * 100) if shop_joints > 0 else 0
            
            # Work order statistics - matching project_summary_tab logic
            # Total sum of joint_size for issued work orders with shop_field='S' and workable='Y'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND LOWER(status) = 'issued' AND UPPER(TRIM(workable)) = 'Y'")
            wo_total_joint_size = cursor.fetchone()[0]
            
            # Balance fit up for issued work orders (remaining to be fit-up) with workable='Y'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND LOWER(status) = 'issued' AND UPPER(TRIM(workable)) = 'Y' AND (fitup_date IS NULL OR TRIM(fitup_date) = '')")
            wo_fitup_balance = cursor.fetchone()[0]
            
            # Fit up done for issued work orders with workable='Y'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND LOWER(status) = 'issued' AND UPPER(TRIM(workable)) = 'Y' AND fitup_date IS NOT NULL AND TRIM(fitup_date) != ''")
            wo_fitup_done = cursor.fetchone()[0]
            
            # Welding done for issued work orders with workable='Y'
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND LOWER(status) = 'issued' AND UPPER(TRIM(workable)) = 'Y' AND welding_date IS NOT NULL AND TRIM(welding_date) != ''")
            wo_welding_done = cursor.fetchone()[0]
            
            # Balance welding = Fit up done - Welding done (remaining welding work)
            wo_welding_balance = wo_fitup_done - wo_welding_done
            
            # Average fit-up done per day
            cursor.execute("""
                SELECT AVG(daily_fitup) FROM (
                    SELECT fitup_date, SUM(joint_size) as daily_fitup 
                    FROM spools 
                    WHERE shop_field = 'S' AND fitup_date IS NOT NULL AND TRIM(fitup_date) != ''
                    GROUP BY fitup_date
                )
            """)
            avg_fitup_per_day = cursor.fetchone()[0] or 0
            
            # Average welding done per day
            cursor.execute("""
                SELECT AVG(daily_welding) FROM (
                    SELECT welding_date, SUM(joint_size) as daily_welding 
                    FROM spools 
                    WHERE shop_field = 'S' AND welding_date IS NOT NULL AND TRIM(welding_date) != ''
                    GROUP BY welding_date
                )
            """)
            avg_welding_per_day = cursor.fetchone()[0] or 0
            
            # Average fit-up done per fitter (based on daily fit-up total divided by daily fitters)
            cursor.execute("""
                SELECT AVG(
                    CASE WHEN mr.total_fitters > 0 THEN daily_fitup / mr.total_fitters 
                         ELSE 0 END
                ) as avg_fitup_per_fitter
                FROM (
                    SELECT fitup_date, SUM(joint_size) as daily_fitup 
                    FROM spools 
                    WHERE shop_field = 'S' AND fitup_date IS NOT NULL AND TRIM(fitup_date) != ''
                    GROUP BY fitup_date
                ) s
                LEFT JOIN manpower_reports mr ON s.fitup_date = mr.date
                WHERE mr.total_fitters IS NOT NULL AND mr.total_fitters > 0
            """)
            avg_fitup_per_fitter_result = cursor.fetchone()
            avg_fitup_per_fitter = avg_fitup_per_fitter_result[0] if avg_fitup_per_fitter_result and avg_fitup_per_fitter_result[0] else 0
            
            # Average welding done per welder (based on daily welding total divided by daily welders)
            cursor.execute("""
                SELECT AVG(
                    CASE WHEN mr.total_welders > 0 THEN daily_welding / mr.total_welders 
                         ELSE 0 END
                ) as avg_welding_per_welder
                FROM (
                    SELECT welding_date, SUM(joint_size) as daily_welding 
                    FROM spools 
                    WHERE shop_field = 'S' AND welding_date IS NOT NULL AND TRIM(welding_date) != ''
                    GROUP BY welding_date
                ) s
                LEFT JOIN manpower_reports mr ON s.welding_date = mr.date
                WHERE mr.total_welders IS NOT NULL AND mr.total_welders > 0
            """)
            avg_welding_per_welder_result = cursor.fetchone()
            avg_welding_per_welder = avg_welding_per_welder_result[0] if avg_welding_per_welder_result and avg_welding_per_welder_result[0] else 0
            
            # Today's fit up total - sum of joint_size for today's date
            today_date = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND fitup_date = ?", (today_date,))
            today_fitup = cursor.fetchone()[0]
            
            # Today's welding total - sum of joint_size for today's date
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND welding_date = ?", (today_date,))
            today_welding = cursor.fetchone()[0]
            
            return [
                {"title": "Total Shop Dia-inch", "value": f"{shop_joints:.2f}", "color": UITheme.PRIMARY_COLOR},
                {"title": "Total Field Dia-inch", "value": f"{field_joints:.2f}", "color": UITheme.SECONDARY_COLOR},
                {"title": "Work Orders", "value": f"{work_orders:,}", "color": UITheme.WARNING_COLOR},
                {"title": "WO Total Dia-Inch", "value": f"{wo_total_joint_size:.2f}", "color": UITheme.PRIMARY_COLOR},
                {"title": "WO Fit-Up Balance", "value": f"{wo_fitup_balance:.2f}", "color": UITheme.WARNING_COLOR if wo_fitup_balance > 0 else UITheme.SUCCESS_COLOR},
                {"title": "WO Welding Balance", "value": f"{wo_welding_balance:.2f}", "color": UITheme.WARNING_COLOR if wo_welding_balance > 0 else UITheme.SUCCESS_COLOR},
                {"title": "Today's Fit-Up", "value": f"{today_fitup:.2f}", "color": UITheme.PRIMARY_COLOR},
                {"title": "Today's Welding", "value": f"{today_welding:.2f}", "color": UITheme.PRIMARY_COLOR},
                {"title": "Fit-Up Done", "value": f"{fitup_completed:.2f}", "color": UITheme.SUCCESS_COLOR},
                {"title": "Welding Done", "value": f"{welding_completed:.2f}", "color": UITheme.SUCCESS_COLOR},
                {"title": "Avg Fit-Up/Day", "value": f"{avg_fitup_per_day:.2f}", "color": UITheme.SECONDARY_COLOR},
                {"title": "Avg Welding/Day", "value": f"{avg_welding_per_day:.2f}", "color": UITheme.SECONDARY_COLOR},
                {"title": "Avg Fit-Up/Fitter", "value": f"{avg_fitup_per_fitter:.2f}", "color": UITheme.SUCCESS_COLOR},
                {"title": "Avg Welding/Welder", "value": f"{avg_welding_per_welder:.2f}", "color": UITheme.SUCCESS_COLOR},
                {"title": "Progress", "value": f"{progress_percentage:.1f}%", "color": UITheme.DANGER_COLOR if progress_percentage < 50 else UITheme.SUCCESS_COLOR}
            ]
    except Exception as e:
        print(f"Database error in get_project_statistics: {e}")
        # Fallback to sample data if database error
        return [
            {"title": "Total Shop Dia-inch", "value": "N/A", "color": UITheme.PRIMARY_COLOR},
            {"title": "Total Field Dia-inch", "value": "N/A", "color": UITheme.SECONDARY_COLOR},
            {"title": "Work Orders", "value": "N/A", "color": UITheme.WARNING_COLOR},
            {"title": "WO Total Dia-Inch", "value": "N/A", "color": UITheme.PRIMARY_COLOR},
            {"title": "WO Fit-Up Balance", "value": "N/A", "color": UITheme.WARNING_COLOR},
            {"title": "WO Welding Balance", "value": "N/A", "color": UITheme.WARNING_COLOR},
            {"title": "Today's Fit-Up", "value": "N/A", "color": UITheme.PRIMARY_COLOR},
            {"title": "Today's Welding", "value": "N/A", "color": UITheme.PRIMARY_COLOR},
            {"title": "Fit-Up Done", "value": "N/A", "color": UITheme.SUCCESS_COLOR},
            {"title": "Welding Done", "value": "N/A", "color": UITheme.SUCCESS_COLOR},
            {"title": "Avg Fit-Up/Day", "value": "N/A", "color": UITheme.SECONDARY_COLOR},
            {"title": "Avg Welding/Day", "value": "N/A", "color": UITheme.SECONDARY_COLOR},
            {"title": "Avg Fit-Up/Fitter", "value": "N/A", "color": UITheme.SUCCESS_COLOR},
            {"title": "Avg Welding/Welder", "value": "N/A", "color": UITheme.SUCCESS_COLOR},
            {"title": "Progress", "value": "N/A", "color": UITheme.DANGER_COLOR}
        ]

def create_stat_card(parent, title, value, color):
    """Create a statistics card widget"""
    card = UITheme.create_styled_frame(parent)
    card.configure(relief="solid", bd=1, padx=25, pady=20)
    
    # Value (large number)
    value_label = tk.Label(card, text=value, font=("Segoe UI", 26, "bold"), 
                          fg=color, bg=UITheme.WHITE_COLOR)
    value_label.pack()
    
    # Title
    title_label = tk.Label(card, text=title, font=("Segoe UI", 12, "normal"), 
                          fg=UITheme.TEXT_COLOR, bg=UITheme.WHITE_COLOR)
    title_label.pack(pady=(8, 0))
    
    # Add hover effect
    def on_enter(e):
        card.configure(bg=UITheme.LIGHT_COLOR)
    
    def on_leave(e):
        card.configure(bg=UITheme.WHITE_COLOR)
    
    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    value_label.bind("<Enter>", on_enter)
    value_label.bind("<Leave>", on_leave)
    title_label.bind("<Enter>", on_enter)
    title_label.bind("<Leave>", on_leave)
    
    return card

def create_activities_tree(parent):
    """Create a treeview for daily activity totals"""
    columns = ("Date", "Activity", "Type")
    tree = UITheme.create_styled_treeview(parent, columns, height=12)
    
    # Configure columns
    tree.heading("Date", text="Date")
    tree.heading("Activity", text="Daily Summary")
    tree.heading("Type", text="Type")
    
    tree.column("Date", width=120, anchor="w")
    tree.column("Activity", width=450, anchor="w")
    tree.column("Type", width=140, anchor="w")
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    return tree

def populate_recent_activities(tree):
    """Populate the activities tree with recent piping project activities"""
    try:
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cursor = conn.cursor()
            
            activities = []
            
            # Get daily fit-up totals (sum of joint_size by date)
            cursor.execute("""
                SELECT fitup_date, 
                       COALESCE(SUM(joint_size), 0) as total_joint_size,
                       COUNT(*) as joint_count
                FROM spools 
                WHERE shop_field = 'S' 
                  AND fitup_date IS NOT NULL 
                  AND fitup_date != '' 
                GROUP BY fitup_date 
                ORDER BY fitup_date DESC 
                LIMIT 7
            """)
            fitup_daily = cursor.fetchall()
            
            for activity in fitup_daily:
                if activity[0]:
                    date_str = activity[0]
                    total_size = activity[1]
                    joint_count = activity[2]
                    
                    # Format date for display
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        if dt.date() == datetime.now().date():
                            display_date = "Today"
                        elif dt.date() == (datetime.now().date() - timedelta(days=1)):
                            display_date = "Yesterday"
                        else:
                            display_date = dt.strftime("%m/%d")
                    except:
                        display_date = date_str[:5] if len(date_str) > 5 else date_str
                    
                    activities.append((
                        date_str,  # For sorting
                        display_date,  # For display
                        f"Fit-Up Done: {total_size:.2f} ({joint_count} joints)",
                        "Daily Total"
                    ))
            
            # Get daily welding totals (sum of joint_size by date)
            cursor.execute("""
                SELECT welding_date, 
                       COALESCE(SUM(joint_size), 0) as total_joint_size,
                       COUNT(*) as joint_count
                FROM spools 
                WHERE shop_field = 'S' 
                  AND welding_date IS NOT NULL 
                  AND welding_date != '' 
                GROUP BY welding_date 
                ORDER BY welding_date DESC 
                LIMIT 7
            """)
            welding_daily = cursor.fetchall()
            
            for activity in welding_daily:
                if activity[0]:
                    date_str = activity[0]
                    total_size = activity[1]
                    joint_count = activity[2]
                    
                    # Format date for display
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        if dt.date() == datetime.now().date():
                            display_date = "Today"
                        elif dt.date() == (datetime.now().date() - timedelta(days=1)):
                            display_date = "Yesterday"
                        else:
                            display_date = dt.strftime("%m/%d")
                    except:
                        display_date = date_str[:5] if len(date_str) > 5 else date_str
                    
                    activities.append((
                        date_str,  # For sorting
                        display_date,  # For display
                        f"Welding Done: {total_size:.2f} ({joint_count} joints)",
                        "Daily Total"
                    ))
            
            # Sort all activities by date (most recent first)
            activities.sort(key=lambda x: x[0], reverse=True)
            
            # Add top 10 activities to tree (display_date, description, type)
            for activity in activities[:10]:
                tree.insert("", "end", values=(activity[1], activity[2], activity[3]))
            
            # If no activities found, show message
            if not activities:
                tree.insert("", "end", values=("N/A", "No recent fit-up or welding activities", "No Data"))
            
    except Exception as e:
        print(f"Error populating daily activities: {e}")
        # Add sample daily activities if database error
        sample_activities = [
            ("Today", "Fit-Up Done: 45.50 (12 joints)", "Daily Total"),
            ("Today", "Welding Done: 38.25 (10 joints)", "Daily Total"),
            ("Yesterday", "Fit-Up Done: 52.00 (15 joints)", "Daily Total"),
            ("Yesterday", "Welding Done: 41.75 (11 joints)", "Daily Total"),
            ("12/08", "Fit-Up Done: 36.50 (9 joints)", "Daily Total"),
            ("12/08", "Welding Done: 29.25 (8 joints)", "Daily Total"),
            ("12/07", "Fit-Up Done: 48.75 (13 joints)", "Daily Total")
        ]
        
        for activity in sample_activities:
            tree.insert("", "end", values=activity)

def create_quick_actions(parent, permissions, dashboard_frame):
    """Create quick action buttons based on user permissions"""
    actions = []
    
    if permissions.get("fitup") or permissions.get("all"):
        actions.append({"text": "🔧 Update Fit-Up", "command": lambda: switch_to_tab("Update Fit-Up")})
    
    if permissions.get("welding") or permissions.get("all"):
        actions.append({"text": "⚡ Update Welding", "command": lambda: switch_to_tab("Update Welding")})
    
    if permissions.get("qc") or permissions.get("all"):
        actions.append({"text": "📋 Generate Report", "command": lambda: switch_to_tab("Generate Reports")})
    
    if permissions.get("all") or permissions.get("pmt"):
        actions.append({"text": "📊 Project Summary", "command": lambda: switch_to_tab("Project Summary")})
    
    if permissions.get("admin") or permissions.get("all"):
        actions.append({"text": "📦 Inventory Tools", "command": lambda: switch_to_tab("Inventory Tools")})
    
    # Always available actions
    actions.extend([
        {"text": "📄 Export Data", "command": export_data},
        {"text": "🔄 Refresh Dashboard", "command": lambda: refresh_dashboard(dashboard_frame)}
    ])
    
    for action in actions:
        btn = UITheme.create_primary_button(parent, action["text"], action["command"], width=18)
        btn.pack(pady=5, padx=8, fill="x")
        btn.configure(font=("Segoe UI", 9, "bold"), pady=6)
        UITheme.apply_button_hover_effect(btn)

def create_progress_visualization(parent):
    """Create a visual progress overview with progress bars based on joint_size sums"""
    try:
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cursor = conn.cursor()
            
            # Get total shop joint_size
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S'")
            shop_joints_total = cursor.fetchone()[0]
            
            if shop_joints_total == 0:
                no_data_label = UITheme.create_body_label(parent, "No shop joint data available")
                no_data_label.pack(pady=10)
                return
            
            # Get completion sums based on joint_size
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND fitup_date IS NOT NULL AND fitup_date != ''")
            fitup_done_total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND welding_date IS NOT NULL AND welding_date != ''")
            welding_done_total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(joint_size), 0) FROM spools WHERE shop_field = 'S' AND site_delivery_date IS NOT NULL AND site_delivery_date != ''")
            delivered_total = cursor.fetchone()[0]
            
            # Calculate percentages based on joint_size
            fitup_percent = (fitup_done_total / shop_joints_total) * 100
            welding_percent = (welding_done_total / shop_joints_total) * 100  
            delivery_percent = (delivered_total / shop_joints_total) * 100
            
            # Create progress bars container
            progress_container = UITheme.create_styled_frame(parent)
            progress_container.pack(fill="x", pady=10, padx=15)
            
            # Fit-up progress
            create_progress_bar(progress_container, "Fit-up Progress:", fitup_percent, f"{fitup_done_total:.2f}/{shop_joints_total:.2f}", 0)
            
            # Welding progress  
            create_progress_bar(progress_container, "Welding Progress:", welding_percent, f"{welding_done_total:.2f}/{shop_joints_total:.2f}", 1)
            
            # Delivery progress
            create_progress_bar(progress_container, "Delivery Progress:", delivery_percent, f"{delivered_total:.2f}/{shop_joints_total:.2f}", 2)
            
    except Exception as e:
        print(f"Error creating progress visualization: {e}")
        error_label = UITheme.create_body_label(parent, "Error loading progress data")
        error_label.pack(pady=10)

def create_progress_bar(parent, label_text, percentage, count_text, row):
    """Create a single progress bar with label - responsive"""
    # Label with responsive sizing
    label = tk.Label(parent, text=label_text, font=("Segoe UI", 11, "bold"), 
                    fg=UITheme.TEXT_COLOR, bg=UITheme.WHITE_COLOR)
    label.grid(row=row, column=0, sticky="w", padx=(0, 15), pady=4)
    
    # Progress bar frame - responsive width
    bar_frame = UITheme.create_styled_frame(parent)
    bar_frame.configure(relief="solid", bd=1, height=30)
    bar_frame.grid(row=row, column=1, sticky="ew", padx=(0, 15), pady=4)
    
    # Configure grid weights for responsive behavior
    parent.grid_columnconfigure(0, weight=0, minsize=150)  # Fixed width for labels
    parent.grid_columnconfigure(1, weight=3, minsize=200)  # Progress bar takes most space
    parent.grid_columnconfigure(2, weight=0, minsize=120)  # Fixed width for percentage text
    
    # Progress fill
    if percentage > 0:
        fill_width = max(1, int(percentage))  # Minimum 1% visible if any progress
        progress_fill = tk.Frame(bar_frame, bg=UITheme.SUCCESS_COLOR if percentage >= 100 else UITheme.SECONDARY_COLOR)
        progress_fill.place(relx=0, rely=0, relheight=1, relwidth=min(percentage/100, 1))
    
    # Progress text
    progress_text = f"{percentage:.1f}% ({count_text})"
    text_label = tk.Label(parent, text=progress_text, font=("Segoe UI", 10, "normal"), 
                         fg=UITheme.TEXT_COLOR, bg=UITheme.WHITE_COLOR)
    text_label.grid(row=row, column=2, sticky="w", padx=(15, 0), pady=4)

def create_system_status(parent):
    """Create system status indicators"""
    status_container = UITheme.create_styled_frame(parent)
    status_container.pack(fill="x", pady=8)
    
    try:
        with sqlite3.connect("database/spool_tracking.db") as conn:
            cursor = conn.cursor()
            
            # Check database connection
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Active users
            cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE active = 1")
            active_users = cursor.fetchone()[0]
            
            # Database status
            db_status = tk.Label(status_container, text=f"● Database: Connected ({table_count} tables)", 
                               font=UITheme.SMALL_FONT, fg=UITheme.SUCCESS_COLOR, bg=UITheme.WHITE_COLOR)
            db_status.pack(side="left", padx=(0, 20))
            
            # Active users status
            users_status = tk.Label(status_container, text=f"● Active Users: {active_users}", 
                                  font=UITheme.SMALL_FONT, fg=UITheme.PRIMARY_COLOR, bg=UITheme.WHITE_COLOR)
            users_status.pack(side="left", padx=(0, 20))
            
            # Current time
            current_time = datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%H:%M:%S")
            time_status = tk.Label(status_container, text=f"● Current Time: {current_time}", 
                                 font=UITheme.SMALL_FONT, fg=UITheme.MUTED_COLOR, bg=UITheme.WHITE_COLOR)
            time_status.pack(side="left")
            
    except Exception as e:
        error_status = tk.Label(status_container, text="● System: Error connecting to database", 
                              font=UITheme.SMALL_FONT, fg=UITheme.DANGER_COLOR, bg=UITheme.WHITE_COLOR)
        error_status.pack(side="left")

def switch_to_tab(tab_name):
    """Helper function to switch to a specific tab"""
    try:
        # Get the main app state from the global scope
        import main
        notebook = main.app_state.notebook
        if notebook:
            # Find and select the tab by name
            for i in range(notebook.index("end")):
                if tab_name.lower() in notebook.tab(i, "text").lower():
                    notebook.select(i)
                    break
        else:
            print(f"Switching to tab: {tab_name}")
    except Exception as e:
        print(f"Could not switch to tab {tab_name}: {e}")

def export_data():
    """Export data functionality - calls existing export functionality"""
    try:
        # Import and call existing export functionality
        import export_master
        export_master.export_to_excel()
        print("Data exported successfully!")
    except Exception as e:
        print(f"Export failed: {e}")

def refresh_dashboard(dashboard_frame):
    """Refresh dashboard data by updating specific components"""
    try:
        if not hasattr(dashboard_frame, 'dashboard_refs'):
            print("Dashboard references not available")
            return
        
        refs = dashboard_frame.dashboard_refs
        
        # Refresh activities tree
        if 'activities_tree' in refs:
            activities_tree = refs['activities_tree']
            # Clear existing activities
            for item in activities_tree.get_children():
                activities_tree.delete(item)
            # Repopulate with fresh data
            populate_recent_activities(activities_tree)
            print("Activities refreshed")
        
        # Refresh statistics cards
        if 'stats_container' in refs:
            stats_container = refs['stats_container']
            permissions = refs.get('permissions', {})
            
            # Clear existing stats cards
            for widget in stats_container.winfo_children():
                widget.destroy()
            
            # Get fresh statistics
            stats_data = get_project_statistics()
            
            # Recreate stats cards
            for i, stat in enumerate(stats_data):
                row = i // 3
                col = i % 3
                card = create_stat_card(stats_container, stat["title"], stat["value"], stat["color"])
                card.grid(row=row, column=col, padx=15, pady=10, sticky="ew")
            
            # Reconfigure grid weights
            for i in range(3):
                stats_container.grid_columnconfigure(i, weight=1, minsize=200)
            for i in range((len(stats_data) + 2) // 3):
                stats_container.grid_rowconfigure(i, weight=1)
            
            print("Statistics refreshed")
        
        # Show success message
        from tkinter import messagebox
        messagebox.showinfo("Success", "Dashboard refreshed successfully!")
        print("Dashboard refresh completed!")
        
    except Exception as e:
        print(f"Error refreshing dashboard: {e}")
        try:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to refresh dashboard: {str(e)}")
        except:
            print("Dashboard refresh failed")