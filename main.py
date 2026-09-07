# main.py

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from PIL import Image, ImageTk
from datetime import datetime
import pytz

# ─── Helper: Resource Path ───────────────────────────────────────────────
def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

# ─── Import Tabs ─────────────────────────────────────────────────────────
from tabs.dashboard_tab import build_tab as build_dashboard_tab  # NEW DASHBOARD TAB
from tabs.update_fitup_tab import build_tab as build_fitup_tab
from tabs.update_welding_tab import build_tab as build_welding_tab
from tabs.painting_delivery_tab import build_tab as build_painting_tab
from tabs.site_delivery_tab import build_tab as build_site_tab
from tabs.fitup_report_tab import build_tab as build_fitup_report_tab
from tabs.visual_report_tab import build_tab as build_visual_report_tab
from tabs.rt_bsr_report_tab import build_tab as build_rt_bsr_tab
from tabs.pwht_report_tab import build_tab as build_pwht_report_tab
from tabs.rt_asr_report_tab import build_tab as build_rt_asr_tab
from tabs.ndt_report_tab import build_tab as build_ndt_report_tab
from tabs.irn_report_tab import build_tab as build_irn_report_tab
from tabs.iso_drawing_tab import build_tab as build_iso_drawing_tab
from tabs.report_tab import build_tab as build_report_tab
from tabs.project_summary_tab import build_project_summary_tab
from tabs.inventory_tab import build_tab as build_inventory_tab
from tabs.generate_fitup_report_tab import build_tab as build_generate_fitup_report_tab  # NEW TAB
from tabs.manpower_report_tab import build_tab as build_manpower_report_tab
from ui_theme import UITheme  # Import UI theme

# ─── Application State ─────────────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.root = None
        self.username = None
        self.permissions = None
        self.login_frame = None
        self.main_frame = None
        self.username_entry = None
        self.password_entry = None
        self.notebook = None  # Store notebook reference for tab switching
        self.login_button = None  # Store login button reference for animation

app_state = AppState()

# ─── Login Logic with Animation ─────────────────────────────────────────────────────────
def authenticate_user():
    username = app_state.username_entry.get().strip()
    password = app_state.password_entry.get().strip()
    
    if not username or not password:
        messagebox.showerror("Login Error", "Please enter both username and password.")
        return
    
    # Disable login button and show loading
    login_btn = app_state.login_button
    login_btn.configure(state="disabled", text="Logging in...")
    
    # Show loading animation
    show_login_animation()
    
    # Perform authentication in background
    app_state.root.after(100, lambda: perform_authentication(username, password))

def perform_authentication(username, password):
    """Perform the actual authentication process"""
    try:
        conn = sqlite3.connect("database/spool_tracking.db")
        cur = conn.cursor()

        try:
            cur.execute("SELECT password, permission FROM user_credentials WHERE username = ?", (username,))
        except sqlite3.OperationalError:
            hide_login_animation()
            messagebox.showerror("Database Error", "Missing user_credentials table.")
            reset_login_button()
            conn.close()
            return

        row = cur.fetchone()

        if row and row[0] == password:
            permission_list = row[1].split(",")
            permissions = {
                "fitup": "Update Fit-Up" in permission_list,
                "welding": "Update Welding" in permission_list,
                "painting": "Painting Delivery" in permission_list,
                "site": "Site Delivery" in permission_list,
                "qc": any(x in permission_list for x in [
                    "Fit-Up Report", "Visual Report", "RT BSR", "PWHT Report", "RT ASR", "NDT Report", "IRN Report"]),
                "admin": "Inventory Tools" in permission_list,
                "all": "all" in permission_list,
                "pmt": "Project Summary" in permission_list,
                "manpower": "Manpower Report" in permission_list
            }

            malaysia_time = datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("INSERT INTO user_log (username, login_time) VALUES (?, ?)", (username, malaysia_time))
            cur.execute("UPDATE user_sessions SET active = 0 WHERE username = ?", (username,))
            cur.execute("INSERT INTO user_sessions (username, login_time, active) VALUES (?, ?, 1)", (username, malaysia_time))

            conn.commit()
            conn.close()

            app_state.username = username
            app_state.permissions = permissions
            
            # Show success animation then transition to main interface
            show_success_animation()
        else:
            conn.close()
            hide_login_animation()
            messagebox.showerror("Login Failed", "Invalid username or password.")
            reset_login_button()
            
    except Exception as e:
        hide_login_animation()
        messagebox.showerror("Error", f"Authentication error: {str(e)}")
        reset_login_button()

def reset_login_button():
    """Reset login button to original state"""
    if hasattr(app_state, 'login_button') and app_state.login_button:
        try:
            app_state.login_button.configure(state="normal", text="Sign In")
        except tk.TclError:
            pass  # Widget might be destroyed

def show_login_animation():
    """Show animated loading during login"""
    # Create loading frame
    app_state.loading_frame = tk.Frame(app_state.login_frame, bg="white")
    app_state.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Loading text
    app_state.loading_label = tk.Label(
        app_state.loading_frame, 
        text="Authenticating...", 
        font=("Arial", 12), 
        bg="white", 
        fg="#3498DB"
    )
    app_state.loading_label.pack(pady=10)
    
    # Progress bar
    app_state.progress_canvas = tk.Canvas(
        app_state.loading_frame, 
        width=200, height=20, 
        bg="white", 
        highlightthickness=0
    )
    app_state.progress_canvas.pack()
    
    # Draw progress bar background
    app_state.progress_canvas.create_rectangle(0, 5, 200, 15, fill="#ECF0F1", outline="#BDC3C7")
    
    # Animate progress bar
    app_state.progress_width = 0
    animate_progress_bar()

def animate_progress_bar():
    """Animate the progress bar during login"""
    if hasattr(app_state, 'progress_canvas') and app_state.progress_width < 200:
        # Clear previous progress
        app_state.progress_canvas.delete("progress")
        
        # Draw current progress
        app_state.progress_canvas.create_rectangle(
            2, 7, app_state.progress_width, 13, 
            fill="#3498DB", outline="", tags="progress"
        )
        
        # Update progress
        app_state.progress_width += 4
        
        # Continue animation
        app_state.root.after(50, animate_progress_bar)

def show_success_animation():
    """Show success animation before transitioning to main interface"""
    if hasattr(app_state, 'loading_label'):
        app_state.loading_label.configure(text="Login Successful!", fg="#27AE60")
    
    # Complete progress bar
    if hasattr(app_state, 'progress_canvas'):
        app_state.progress_canvas.delete("progress")
        app_state.progress_canvas.create_rectangle(
            2, 7, 198, 13, 
            fill="#27AE60", outline=""
        )
    
    # Add checkmark
    if hasattr(app_state, 'loading_frame'):
        checkmark = tk.Label(
            app_state.loading_frame, 
            text="✓", 
            font=("Arial", 16, "bold"), 
            bg="white", 
            fg="#27AE60"
        )
        checkmark.pack(pady=5)
    
    # Transition to main interface after delay
    app_state.root.after(1500, transition_to_main_interface)

def hide_login_animation():
    """Hide login animation elements"""
    if hasattr(app_state, 'loading_frame'):
        app_state.loading_frame.destroy()
        delattr(app_state, 'loading_frame')
    if hasattr(app_state, 'loading_label'):
        delattr(app_state, 'loading_label')
    if hasattr(app_state, 'progress_canvas'):
        delattr(app_state, 'progress_canvas')

def transition_to_main_interface():
    """Smooth transition from login to main interface"""
    hide_login_animation()
    
    # Fade out login frame
    fade_out_login()

def fade_out_login():
    """Fade out login interface"""
    # Start fade transition
    app_state.fade_alpha = 1.0
    fade_step()

def fade_step():
    """Single step in fade animation"""
    if app_state.fade_alpha > 0:
        app_state.fade_alpha -= 0.05
        
        # Continue fade animation
        app_state.root.after(30, fade_step)
    else:
        # Fade complete, show main interface
        show_main_interface_animated()

def show_main_interface_animated():
    """Show main interface with fade-in animation"""
    # Hide login frame and show main frame
    app_state.login_frame.pack_forget()
    app_state.main_frame.pack(fill="both", expand=True)
    
    # Update window title
    app_state.root.title("Piping Work Order & QC System")
    
    # Build the main interface
    build_main_interface()
    
    # Fade in main interface
    app_state.main_frame.configure(bg="white")
    fade_in_main()

def fade_in_main():
    """Fade in main interface"""
    # Simple fade-in effect by showing content gradually
    welcome_label = tk.Label(
        app_state.main_frame, 
        text=f"Welcome, {app_state.username}!", 
        font=("Arial", 16), 
        bg="white", 
        fg="#27AE60"
    )
    welcome_label.place(relx=0.5, rely=0.1, anchor="center")
    
    # Remove welcome message after 2 seconds
    app_state.root.after(2000, lambda: welcome_label.destroy())

# ─── Show Main Interface ────────────────────────────────────────────────────
def show_main_interface():
    # Hide login frame and show main frame
    app_state.login_frame.pack_forget()
    app_state.main_frame.pack(fill="both", expand=True)
    
    # Update window title and show user info
    app_state.root.title("Piping Work Order & QC System")
    
    # Build the main interface within the existing main_frame
    build_main_interface()

# ─── Build Main Interface ───────────────────────────────────────────────────
def build_main_interface():
    # Clear any existing content in main_frame
    for widget in app_state.main_frame.winfo_children():
        widget.destroy()

    # Header frame with logos and user info
    header_frame = tk.Frame(app_state.main_frame)
    header_frame.pack(pady=10, fill="x")
    
    # Configure grid weights for proper spacing
    header_frame.grid_columnconfigure(1, weight=1)
    
    left_logo_img = ImageTk.PhotoImage(Image.open(get_resource_path("NAEC logo.jpg")).resize((120, 70)))
    right_logo_img = ImageTk.PhotoImage(Image.open(get_resource_path("MIE.png")).resize((120, 70)))
    
    tk.Label(header_frame, image=left_logo_img).grid(row=0, column=0, padx=20)
    tk.Label(header_frame, text="TEAM PIPING", font=("Helvetica", 20, "bold")).grid(row=0, column=1, padx=20)
    tk.Label(header_frame, image=right_logo_img).grid(row=0, column=2, padx=20)
    
    # User info and logout button frame
    user_frame = tk.Frame(header_frame)
    user_frame.grid(row=0, column=3, sticky="e", padx=20)
    
    # Status indicator
    status_frame = tk.Frame(user_frame)
    status_frame.pack(side="left", padx=(0,15))
    
    status_dot = tk.Label(status_frame, text="●", font=("Arial", 12), fg="#27AE60")
    status_dot.pack(side="left")
    
    tk.Label(status_frame, text=f"Logged in as: {app_state.username}", font=("Arial", 10), fg="#2C3E50").pack(side="left", padx=(5,0))
    
    # Logout button with hover effect
    logout_btn = tk.Button(user_frame, text="Sign Out", command=logout_user, 
                          font=("Arial", 9, "bold"), bg="#E74C3C", fg="white", 
                          relief="flat", bd=0, padx=15, pady=5, cursor="hand2")
    logout_btn.pack(side="right")
    
    # Add hover effect for logout button
    def logout_on_enter(e):
        logout_btn.configure(bg="#C0392B")
    
    def logout_on_leave(e):
        logout_btn.configure(bg="#E74C3C")
    
    logout_btn.bind("<Enter>", logout_on_enter)
    logout_btn.bind("<Leave>", logout_on_leave)
    
    # Store images to prevent garbage collection
    app_state.main_frame.left_logo_img = left_logo_img
    app_state.main_frame.right_logo_img = right_logo_img
    
    # Apply enhanced UI theme to notebook
    UITheme.setup_main_window_style(app_state.root)
    
    # Notebook for tabs with enhanced styling
    notebook = ttk.Notebook(app_state.main_frame, style="Custom.TNotebook")
    notebook.pack(fill="both", expand=True, padx=10, pady=(0,10))

    # Add tabs based on permissions
    permissions = app_state.permissions
    
    # Always add dashboard as first tab
    notebook.add(build_dashboard_tab(notebook, permissions), text="📊 Dashboard")
    
    if permissions.get("fitup") or permissions.get("all"):
        notebook.add(build_fitup_tab(notebook, permissions), text="🔧 Update Fit-Up")
    if permissions.get("welding") or permissions.get("all"):
        notebook.add(build_welding_tab(notebook, permissions), text="⚡ Update Welding")
    if permissions.get("painting") or permissions.get("all"):
        notebook.add(build_painting_tab(notebook, permissions), text="🎨 Painting Delivery")
    if permissions.get("site") or permissions.get("all"):
        notebook.add(build_site_tab(notebook, permissions), text="🚚 Site Delivery")
    if permissions.get("qc") or permissions.get("all"):
        notebook.add(build_fitup_report_tab(notebook, permissions), text="📋 Fit-Up Report")
        notebook.add(build_generate_fitup_report_tab(notebook, permissions), text="📄 Generate Fit-Up Report")
        notebook.add(build_visual_report_tab(notebook, permissions), text="👁️ Visual Report")
        notebook.add(build_rt_bsr_tab(notebook, permissions), text="🔬 RT BSR")
        notebook.add(build_pwht_report_tab(notebook, permissions), text="🔥 PWHT Report")
        notebook.add(build_rt_asr_tab(notebook, permissions), text="📊 RT ASR")
        notebook.add(build_ndt_report_tab(notebook, permissions), text="🔍 NDT Report")
        notebook.add(build_irn_report_tab(notebook, permissions), text="📝 IRN Report")
    if permissions.get("all") or permissions.get("pmt"):
        notebook.add(build_iso_drawing_tab(notebook, permissions), text="📐 ISO Drawing")
        notebook.add(build_report_tab(notebook, permissions), text="📊 Generate Reports")
        notebook.add(build_project_summary_tab(notebook, permissions), text="📈 Project Summary")
    if permissions.get("admin") or permissions.get("all"):
        notebook.add(build_inventory_tab(notebook, permissions), text="📦 Inventory Tools")
    if permissions.get("manpower") or permissions.get("admin") or permissions.get("all"):
        notebook.add(build_manpower_report_tab(notebook, permissions), text="👷 Manpower Report")
    
    # Store notebook reference for potential tab switching
    app_state.notebook = notebook

# ─── Logout Function ────────────────────────────────────────────────────────
def logout_user():
    # Update database
    conn = sqlite3.connect("database/spool_tracking.db")
    conn.execute("UPDATE user_sessions SET active = 0 WHERE username = ?", (app_state.username,))
    conn.commit()
    conn.close()
    
    # Reset app state
    app_state.username = None
    app_state.permissions = None
    
    # Clear entry fields
    app_state.username_entry.delete(0, tk.END)
    app_state.password_entry.delete(0, tk.END)
    
    # Reset login button state and cleanup animations
    reset_login_interface()
    
    # Show login interface
    show_login_interface()

def reset_login_interface():
    """Reset login interface to initial state after logout"""
    # Reset login button
    if hasattr(app_state, 'login_button') and app_state.login_button:
        try:
            app_state.login_button.configure(state="normal", text="Sign In")
        except tk.TclError:
            pass  # Widget might be destroyed
    
    # Clean up any remaining animation elements
    cleanup_all_animations()
    
    # Reset animation state variables
    if hasattr(app_state, 'progress_width'):
        delattr(app_state, 'progress_width')
    if hasattr(app_state, 'fade_alpha'):
        delattr(app_state, 'fade_alpha')
    if hasattr(app_state, 'logo_scale'):
        delattr(app_state, 'logo_scale')
    if hasattr(app_state, 'logo_direction'):
        delattr(app_state, 'logo_direction')

def cleanup_all_animations():
    """Clean up all animation elements"""
    # Clean up loading animation elements
    if hasattr(app_state, 'loading_frame'):
        try:
            app_state.loading_frame.destroy()
        except tk.TclError:
            pass
        delattr(app_state, 'loading_frame')
    
    if hasattr(app_state, 'loading_label'):
        delattr(app_state, 'loading_label')
    
    if hasattr(app_state, 'progress_canvas'):
        delattr(app_state, 'progress_canvas')
    
    # Clean up any other animation references
    animation_attrs = ['naec_logo', 'title_label', 'mie_logo']
    for attr in animation_attrs:
        if hasattr(app_state, attr):
            delattr(app_state, attr)

# ─── Show Login Interface ──────────────────────────────────────────────────
def show_login_interface():
    # Hide main frame and show login frame
    app_state.main_frame.pack_forget()
    app_state.login_frame.pack(fill="both", expand=True)
    
    # Update window title
    app_state.root.title("Login - TEAM PIPING")
    
    # Restart logo animation if returning from logout
    if hasattr(app_state, 'title_label') and app_state.title_label and app_state.title_label.winfo_exists():
        # Reset animation variables and restart
        if not hasattr(app_state, 'logo_scale'):
            app_state.logo_scale = 1.0
            app_state.logo_direction = 1
            pulse_logos()

# ─── Create Login Interface ────────────────────────────────────────────────
def create_login_interface():
    app_state.login_frame = tk.Frame(app_state.root, bg="white")
    
    # Main container for centering
    main_container = tk.Frame(app_state.login_frame, bg="white")
    main_container.pack(expand=True, fill="both")
    
    # Login card frame
    login_card = tk.Frame(main_container, bg="white", relief="solid", bd=1, padx=40, pady=40)
    login_card.place(relx=0.5, rely=0.5, anchor="center")
    
    # Logo header frame
    header_frame = tk.Frame(login_card, bg="white")
    header_frame.pack(pady=(0, 30))
    
    naec_img = ImageTk.PhotoImage(Image.open(get_resource_path("NAEC logo.jpg")).resize((100, 60)))
    mie_img = ImageTk.PhotoImage(Image.open(get_resource_path("MIE.png")).resize((100, 60)))
    
    # Create logo labels with initial transparency effect
    app_state.naec_logo = tk.Label(header_frame, image=naec_img, bg="white")
    app_state.naec_logo.grid(row=0, column=0, padx=10)
    
    app_state.title_label = tk.Label(header_frame, text="TEAM PIPING", font=("Helvetica", 22, "bold"), bg="white", fg="#2C3E50")
    app_state.title_label.grid(row=0, column=1, padx=15)
    
    app_state.mie_logo = tk.Label(header_frame, image=mie_img, bg="white")
    app_state.mie_logo.grid(row=0, column=2, padx=10)
    
    # Store images to prevent garbage collection
    app_state.login_frame.naec_img = naec_img
    app_state.login_frame.mie_img = mie_img
    
    # Start logo animation
    animate_login_logos()
    
    # Login form
    form_frame = tk.Frame(login_card, bg="white")
    form_frame.pack(pady=10)
    
    # Welcome message
    tk.Label(form_frame, text="Welcome! Please sign in to continue.", font=("Arial", 11), bg="white", fg="#7F8C8D").pack(pady=(0, 20))
    
    # Username field
    tk.Label(form_frame, text="Username", font=("Arial", 10, "bold"), bg="white", fg="#2C3E50").pack(anchor="w", pady=(0, 5))
    app_state.username_entry = tk.Entry(form_frame, width=35, font=("Arial", 11), relief="solid", bd=1, highlightthickness=1, highlightcolor="#3498DB")
    app_state.username_entry.pack(pady=(0, 15), ipady=8)
    
    # Password field
    tk.Label(form_frame, text="Password", font=("Arial", 10, "bold"), bg="white", fg="#2C3E50").pack(anchor="w", pady=(0, 5))
    app_state.password_entry = tk.Entry(form_frame, show="*", width=35, font=("Arial", 11), relief="solid", bd=1, highlightthickness=1, highlightcolor="#3498DB")
    app_state.password_entry.pack(pady=(0, 25), ipady=8)
    
    # Login button
    app_state.login_button = tk.Button(form_frame, text="Sign In", command=authenticate_user, 
                                      width=25, font=("Arial", 11, "bold"), 
                                      bg="#3498DB", fg="white", relief="flat", bd=0, 
                                      pady=12, cursor="hand2")
    app_state.login_button.pack()
    
    # Add hover effect for login button
    def on_enter(e):
        if app_state.login_button['state'] == 'normal':
            app_state.login_button.configure(bg="#2980B9")
    
    def on_leave(e):
        if app_state.login_button['state'] == 'normal':
            app_state.login_button.configure(bg="#3498DB")
    
    app_state.login_button.bind("<Enter>", on_enter)
    app_state.login_button.bind("<Leave>", on_leave)
    
    # Bind Enter key to login
    app_state.root.bind('<Return>', lambda event: authenticate_user())
    
    # Focus on username entry
    app_state.username_entry.focus_set()

def animate_login_logos():
    """Animate login logos with subtle pulsing effect"""
    app_state.logo_scale = 1.0
    app_state.logo_direction = 1
    pulse_logos()

def pulse_logos():
    """Create pulsing effect on login logos"""
    if not hasattr(app_state, 'title_label'):
        return
    
    try:
        # Calculate scale
        app_state.logo_scale += app_state.logo_direction * 0.02
        
        if app_state.logo_scale > 1.1:
            app_state.logo_direction = -1
        elif app_state.logo_scale < 0.95:
            app_state.logo_direction = 1
        
        # Apply subtle color change to title
        intensity = int(255 * (0.8 + 0.2 * ((app_state.logo_scale - 0.95) / 0.15)))
        color = f"#{min(44, int(44 * app_state.logo_scale)):02x}{min(62, int(62 * app_state.logo_scale)):02x}{min(80, int(80 * app_state.logo_scale)):02x}"
        
        if hasattr(app_state, 'title_label') and app_state.title_label.winfo_exists():
            app_state.title_label.configure(fg=color)
        
        # Continue animation
        app_state.root.after(100, pulse_logos)
        
    except tk.TclError:
        # Widget was destroyed, stop animation
        pass

# ─── Initialize Application ─────────────────────────────────────────────────
def initialize_app():
    app_state.root = tk.Tk()
    app_state.root.title("Login - TEAM PIPING")
    app_state.root.geometry("1000x700")
    app_state.root.configure(bg="white")
    
    # Center the window
    app_state.root.geometry("+%d+%d" % ((app_state.root.winfo_screenwidth()/2 - 500), (app_state.root.winfo_screenheight()/2 - 350)))
    
    def on_close():
        if app_state.username:
            conn = sqlite3.connect("database/spool_tracking.db")
            conn.execute("UPDATE user_sessions SET active = 0 WHERE username = ?", (app_state.username,))
            conn.commit()
            conn.close()
        app_state.root.destroy()
    
    app_state.root.protocol("WM_DELETE_WINDOW", on_close)
    
    # Create main frame (hidden initially)
    app_state.main_frame = tk.Frame(app_state.root, bg="white")
    
    # Create and show login interface
    create_login_interface()
    show_login_interface()
    
    app_state.root.mainloop()

# ─── Start Application ──────────────────────────────────────────────────────
if __name__ == "__main__":
    initialize_app()
