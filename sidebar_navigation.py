"""
Sidebar Navigation Component for TEAM PIPING
Optional alternative to tabbed interface
"""

import tkinter as tk
from tkinter import ttk
from ui_theme import UITheme

class SidebarNavigation:
    def __init__(self, parent, notebook, permissions):
        self.parent = parent
        self.notebook = notebook
        self.permissions = permissions
        self.current_selection = 0
        
        # Create sidebar frame
        self.sidebar = UITheme.create_styled_frame(parent)
        self.sidebar.configure(bg=UITheme.LIGHT_COLOR, relief="solid", bd=1, width=220)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)  # Maintain fixed width
        
        # Sidebar header
        self.create_header()
        
        # Navigation items
        self.nav_items = []
        self.nav_buttons = []
        
        # Create navigation items based on permissions
        self.create_navigation_items()
        
    def create_header(self):
        """Create sidebar header"""
        header_frame = UITheme.create_styled_frame(self.sidebar)
        header_frame.configure(bg=UITheme.LIGHT_COLOR)
        header_frame.pack(fill="x", pady=15, padx=10)
        
        title = UITheme.create_subtitle_label(header_frame, "Navigation")
        title.configure(bg=UITheme.LIGHT_COLOR)
        title.pack(anchor="w")
        
        # Separator line
        separator = tk.Frame(header_frame, height=1, bg=UITheme.MUTED_COLOR)
        separator.pack(fill="x", pady=(10, 0))
        
    def create_navigation_items(self):
        """Create navigation items based on permissions"""
        # Always include dashboard
        self.add_nav_item("📊 Dashboard", 0)
        
        if self.permissions.get("fitup") or self.permissions.get("all"):
            self.add_nav_item("🔧 Update Fit-Up", len(self.nav_items))
            
        if self.permissions.get("welding") or self.permissions.get("all"):
            self.add_nav_item("⚡ Update Welding", len(self.nav_items))
            
        if self.permissions.get("painting") or self.permissions.get("all"):
            self.add_nav_item("🎨 Painting Delivery", len(self.nav_items))
            
        if self.permissions.get("site") or self.permissions.get("all"):
            self.add_nav_item("🚚 Site Delivery", len(self.nav_items))
            
        # QC Reports submenu
        if self.permissions.get("qc") or self.permissions.get("all"):
            self.add_nav_separator("QC Reports")
            self.add_nav_item("📋 Fit-Up Report", len(self.nav_items))
            self.add_nav_item("👁️ Visual Report", len(self.nav_items))
            self.add_nav_item("🔬 RT BSR", len(self.nav_items))
            self.add_nav_item("🔥 PWHT Report", len(self.nav_items))
            
        # Management section
        if self.permissions.get("all") or self.permissions.get("pmt"):
            self.add_nav_separator("Management")
            self.add_nav_item("📐 ISO Drawing", len(self.nav_items))
            self.add_nav_item("📊 Generate Reports", len(self.nav_items))
            self.add_nav_item("📈 Project Summary", len(self.nav_items))
            
        if self.permissions.get("admin") or self.permissions.get("all"):
            self.add_nav_item("📦 Inventory Tools", len(self.nav_items))
            
    def add_nav_separator(self, text):
        """Add a separator with text"""
        sep_frame = UITheme.create_styled_frame(self.sidebar)
        sep_frame.configure(bg=UITheme.LIGHT_COLOR)
        sep_frame.pack(fill="x", pady=(15, 5), padx=10)
        
        sep_label = tk.Label(sep_frame, text=text, font=UITheme.SMALL_FONT,
                           fg=UITheme.MUTED_COLOR, bg=UITheme.LIGHT_COLOR)
        sep_label.pack(anchor="w")
        
        line = tk.Frame(sep_frame, height=1, bg=UITheme.MUTED_COLOR)
        line.pack(fill="x", pady=(2, 0))
        
    def add_nav_item(self, text, tab_index):
        """Add a navigation item"""
        self.nav_items.append({"text": text, "tab_index": tab_index})
        
        btn = tk.Button(self.sidebar, text=text, 
                       command=lambda idx=tab_index: self.select_tab(idx),
                       font=UITheme.BODY_FONT, bg=UITheme.WHITE_COLOR, 
                       fg=UITheme.TEXT_COLOR, relief="flat", bd=0, 
                       padx=15, pady=8, anchor="w", cursor="hand2")
        btn.pack(fill="x", padx=5, pady=1)
        
        self.nav_buttons.append(btn)
        
        # Add hover effect
        def on_enter(e, button=btn):
            if button != self.get_current_button():
                button.configure(bg=UITheme.SECONDARY_COLOR, fg=UITheme.WHITE_COLOR)
        
        def on_leave(e, button=btn):
            if button != self.get_current_button():
                button.configure(bg=UITheme.WHITE_COLOR, fg=UITheme.TEXT_COLOR)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
    def select_tab(self, tab_index):
        """Select a tab and update button states"""
        if tab_index < self.notebook.index("end"):
            # Update button states
            self.update_button_states(tab_index)
            
            # Select the tab
            self.notebook.select(tab_index)
            self.current_selection = tab_index
            
    def update_button_states(self, selected_index):
        """Update button visual states"""
        for i, btn in enumerate(self.nav_buttons):
            if i == selected_index:
                btn.configure(bg=UITheme.PRIMARY_COLOR, fg=UITheme.WHITE_COLOR)
            else:
                btn.configure(bg=UITheme.WHITE_COLOR, fg=UITheme.TEXT_COLOR)
                
    def get_current_button(self):
        """Get the currently selected button"""
        if self.current_selection < len(self.nav_buttons):
            return self.nav_buttons[self.current_selection]
        return None
        
    def toggle_visibility(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", padx=(0, 10))

def create_sidebar_layout(main_frame, notebook, permissions):
    """Create a layout with sidebar navigation"""
    # Create container for sidebar and content
    content_container = UITheme.create_styled_frame(main_frame)
    content_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    # Create sidebar
    sidebar = SidebarNavigation(content_container, notebook, permissions)
    
    # Move notebook to the right side of the sidebar
    notebook.pack_forget()  # Remove from original position
    notebook.pack(in_=content_container, side="right", fill="both", expand=True)
    
    return sidebar

# Example usage and testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sidebar Navigation Test")
    root.geometry("1200x700")
    UITheme.setup_main_window_style(root)
    
    # Create test notebook
    notebook = ttk.Notebook(root, style="Custom.TNotebook")
    
    # Add some test tabs
    for i in range(5):
        frame = UITheme.create_styled_frame(notebook)
        label = UITheme.create_title_label(frame, f"Content {i+1}")
        label.pack(pady=50)
        notebook.add(frame, text=f"Tab {i+1}")
    
    # Test permissions
    test_permissions = {"fitup": True, "welding": True, "qc": True, "admin": True}
    
    # Create sidebar layout
    sidebar = create_sidebar_layout(root, notebook, test_permissions)
    
    print("Sidebar navigation test started...")
    print("Click sidebar items to switch between tabs")
    
    root.mainloop()