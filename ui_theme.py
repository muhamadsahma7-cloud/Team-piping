import tkinter as tk
from tkinter import ttk

class UITheme:
    # Color palette
    PRIMARY_COLOR = "#2C3E50"      # Dark blue-gray
    SECONDARY_COLOR = "#3498DB"    # Light blue
    SUCCESS_COLOR = "#27AE60"      # Green
    WARNING_COLOR = "#F39C12"      # Orange
    DANGER_COLOR = "#E74C3C"       # Red
    LIGHT_COLOR = "#ECF0F1"        # Light gray
    WHITE_COLOR = "#FFFFFF"        # White
    TEXT_COLOR = "#2C3E50"         # Dark text
    MUTED_COLOR = "#7F8C8D"        # Muted gray
    
    # Fonts
    TITLE_FONT = ("Segoe UI", 16, "bold")
    SUBTITLE_FONT = ("Segoe UI", 12, "bold")
    BODY_FONT = ("Segoe UI", 10)
    SMALL_FONT = ("Segoe UI", 9)
    CODE_FONT = ("Consolas", 10)
    
    # Dimensions
    BUTTON_WIDTH = 30
    ENTRY_WIDTH = 25
    LISTBOX_HEIGHT = 8
    TEXT_AREA_HEIGHT = 25
    
    # Padding
    MAIN_PADDING = 15
    SECTION_PADDING = 10
    WIDGET_PADDING = 5

    @staticmethod
    def create_title_label(parent, text, font=None):
        if font is None:
            font = UITheme.TITLE_FONT
        label = tk.Label(
            parent, 
            text=text, 
            font=font,
            fg=UITheme.PRIMARY_COLOR,
            bg=UITheme.WHITE_COLOR
        )
        return label
    
    @staticmethod
    def create_subtitle_label(parent, text):
        label = tk.Label(
            parent,
            text=text,
            font=UITheme.SUBTITLE_FONT,
            fg=UITheme.SECONDARY_COLOR,
            bg=UITheme.WHITE_COLOR
        )
        return label
    
    @staticmethod
    def create_body_label(parent, text):
        label = tk.Label(
            parent,
            text=text,
            font=UITheme.BODY_FONT,
            fg=UITheme.TEXT_COLOR,
            bg=UITheme.WHITE_COLOR
        )
        return label
    
    @staticmethod
    def create_primary_button(parent, text, command=None, width=None):
        if width is None:
            width = UITheme.BUTTON_WIDTH
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.PRIMARY_COLOR,
            fg=UITheme.WHITE_COLOR,
            activebackground=UITheme.SECONDARY_COLOR,
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_success_button(parent, text, command=None, width=None):
        if width is None:
            width = UITheme.BUTTON_WIDTH
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.SUCCESS_COLOR,
            fg=UITheme.WHITE_COLOR,
            activebackground="#219A52",
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_warning_button(parent, text, command=None, width=None):
        if width is None:
            width = UITheme.BUTTON_WIDTH
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.WARNING_COLOR,
            fg=UITheme.WHITE_COLOR,
            activebackground="#E67E22",
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_danger_button(parent, text, command=None, width=None):
        if width is None:
            width = UITheme.BUTTON_WIDTH
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.DANGER_COLOR,
            fg=UITheme.WHITE_COLOR,
            activebackground="#C0392B",
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_secondary_button(parent, text, command=None, width=None):
        if width is None:
            width = UITheme.BUTTON_WIDTH
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.LIGHT_COLOR,
            fg=UITheme.TEXT_COLOR,
            activebackground=UITheme.MUTED_COLOR,
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=1,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_styled_entry(parent, textvariable=None, width=None):
        if width is None:
            width = UITheme.ENTRY_WIDTH
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            font=UITheme.BODY_FONT,
            width=width,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=UITheme.SECONDARY_COLOR
        )
        return entry
    
    @staticmethod
    def create_styled_listbox(parent, height=None, selectmode=tk.SINGLE):
        if height is None:
            height = UITheme.LISTBOX_HEIGHT
        listbox = tk.Listbox(
            parent,
            height=height,
            selectmode=selectmode,
            font=UITheme.BODY_FONT,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=UITheme.SECONDARY_COLOR,
            selectbackground=UITheme.SECONDARY_COLOR,
            selectforeground=UITheme.WHITE_COLOR
        )
        return listbox
    
    @staticmethod
    def create_styled_text(parent, width=60, height=None, bg_color=None):
        if height is None:
            height = UITheme.TEXT_AREA_HEIGHT
        if bg_color is None:
            bg_color = UITheme.LIGHT_COLOR
        text = tk.Text(
            parent,
            width=width,
            height=height,
            font=UITheme.CODE_FONT,
            bg=bg_color,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=UITheme.SECONDARY_COLOR
        )
        return text
    
    @staticmethod
    def create_styled_frame(parent, bg_color=None):
        if bg_color is None:
            bg_color = UITheme.WHITE_COLOR
        frame = tk.Frame(parent, bg=bg_color)
        return frame
    
    @staticmethod
    def create_section_frame(parent, title=None):
        frame = UITheme.create_styled_frame(parent)
        frame.configure(relief="solid", bd=1, padx=UITheme.SECTION_PADDING, pady=UITheme.SECTION_PADDING)
        
        if title:
            title_label = UITheme.create_subtitle_label(frame, title)
            title_label.pack(anchor="w", pady=(0, UITheme.WIDGET_PADDING))
        
        return frame
    
    @staticmethod
    def create_styled_combobox(parent, values=None, width=None, state="readonly"):
        if width is None:
            width = UITheme.ENTRY_WIDTH
        
        style = ttk.Style()
        style.configure(
            "Custom.TCombobox",
            fieldbackground=UITheme.WHITE_COLOR,
            background=UITheme.WHITE_COLOR,
            foreground=UITheme.TEXT_COLOR,
            borderwidth=1,
            relief="solid"
        )
        
        combo = ttk.Combobox(
            parent,
            values=values or [],
            width=width,
            state=state,
            style="Custom.TCombobox",
            font=UITheme.BODY_FONT
        )
        return combo
    
    @staticmethod
    def create_styled_treeview(parent, columns, show="headings", height=10):
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background=UITheme.WHITE_COLOR,
            foreground=UITheme.TEXT_COLOR,
            fieldbackground=UITheme.WHITE_COLOR,
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=UITheme.PRIMARY_COLOR,
            foreground=UITheme.WHITE_COLOR,
            font=UITheme.SUBTITLE_FONT
        )
        
        tree = ttk.Treeview(
            parent,
            columns=columns,
            show=show,
            height=height,
            style="Custom.Treeview"
        )
        return tree
    
    @staticmethod
    def apply_button_hover_effect(button, hover_color=None, normal_color=None):
        if hover_color is None:
            hover_color = UITheme.SECONDARY_COLOR
        if normal_color is None:
            normal_color = button.cget("bg")
        
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    @staticmethod
    def create_icon_button(parent, text, command=None, width=None, icon_color=None):
        """Create a button with icon and text"""
        if width is None:
            width = UITheme.BUTTON_WIDTH
        if icon_color is None:
            icon_color = UITheme.WHITE_COLOR
            
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=UITheme.BODY_FONT,
            bg=UITheme.PRIMARY_COLOR,
            fg=icon_color,
            activebackground=UITheme.SECONDARY_COLOR,
            activeforeground=UITheme.WHITE_COLOR,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            width=width,
            cursor="hand2"
        )
        return button
    
    @staticmethod
    def create_info_card(parent, title, content, bg_color=None):
        """Create an information card widget"""
        if bg_color is None:
            bg_color = UITheme.LIGHT_COLOR
            
        card = UITheme.create_styled_frame(parent)
        card.configure(relief="solid", bd=1, padx=15, pady=15, bg=bg_color)
        
        if title:
            title_label = UITheme.create_subtitle_label(card, title)
            title_label.configure(bg=bg_color)
            title_label.pack(anchor="w", pady=(0, 5))
        
        content_label = UITheme.create_body_label(card, content)
        content_label.configure(bg=bg_color)
        content_label.pack(anchor="w")
        
        return card
    
    @staticmethod
    def create_status_indicator(parent, status_text, status_type="info"):
        """Create a status indicator with appropriate color"""
        color_map = {
            "success": UITheme.SUCCESS_COLOR,
            "warning": UITheme.WARNING_COLOR,
            "error": UITheme.DANGER_COLOR,
            "info": UITheme.SECONDARY_COLOR
        }
        
        color = color_map.get(status_type, UITheme.PRIMARY_COLOR)
        
        indicator = tk.Label(
            parent,
            text=f"● {status_text}",
            font=UITheme.SMALL_FONT,
            fg=color,
            bg=UITheme.WHITE_COLOR
        )
        return indicator

    @staticmethod
    def setup_main_window_style(root):
        root.configure(bg=UITheme.WHITE_COLOR)
        
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure notebook (tabs) with enhanced styling
        style.configure(
            "Custom.TNotebook",
            background=UITheme.WHITE_COLOR,
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Custom.TNotebook.Tab",
            background=UITheme.LIGHT_COLOR,
            foreground=UITheme.TEXT_COLOR,
            padding=[15, 8],
            font=UITheme.BODY_FONT,
            borderwidth=1,
            relief="solid"
        )
        style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", UITheme.PRIMARY_COLOR), ("active", UITheme.SECONDARY_COLOR)],
            foreground=[("selected", UITheme.WHITE_COLOR), ("active", UITheme.WHITE_COLOR)],
            relief=[("selected", "raised"), ("active", "raised")]
        )
        
        # Configure treeview headers
        style.configure(
            "Custom.Treeview.Heading",
            background=UITheme.PRIMARY_COLOR,
            foreground=UITheme.WHITE_COLOR,
            font=UITheme.SUBTITLE_FONT,
            relief="flat"
        )
        
        # Configure progressbar if needed
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=UITheme.SUCCESS_COLOR,
            troughcolor=UITheme.LIGHT_COLOR,
            borderwidth=0,
            lightcolor=UITheme.SUCCESS_COLOR,
            darkcolor=UITheme.SUCCESS_COLOR
        )