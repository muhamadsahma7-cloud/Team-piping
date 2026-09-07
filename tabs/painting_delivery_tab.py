import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = tk.Frame(parent, padx=10, pady=10)

    # ─── Load Data ───
    with sqlite3.connect("database/spool_tracking.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT iso_dwg_no FROM spools WHERE shop_field = 'S'")
        all_iso = sorted(row[0] for row in cur.fetchall())
        cur.execute("SELECT iso_dwg_no, line_no, iso_run_no, dwg_spool_no FROM spools WHERE shop_field = 'S'")
        iso_data = cur.fetchall()

    # ─── Widgets ───
    tk.Label(frame, text="Type ISO DWG NO").pack(anchor="w")
    iso_var = tk.StringVar()
    iso_entry = tk.Entry(frame, textvariable=iso_var, width=40)
    iso_entry.pack(anchor="w", pady=2)

    iso_listbox = tk.Listbox(frame, height=5, width=40)
    iso_listbox.pack(anchor="w", pady=(0,5))
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=iso_listbox.yview)
    iso_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.place(in_=iso_listbox, relx=1.0, relheight=1.0, anchor="ne")

    tk.Label(frame, text="LINE NO").pack(anchor="w", pady=(5,0))
    line_combo = ttk.Combobox(frame, width=40)
    line_combo.pack(anchor="w", pady=2)

    tk.Label(frame, text="PAGE NO").pack(anchor="w", pady=(5,0))
    page_combo = ttk.Combobox(frame, width=40)
    page_combo.pack(anchor="w", pady=2)

    tk.Label(frame, text="DWG SPOOL NO").pack(anchor="w", pady=(5,0))
    spool_combo = ttk.Combobox(frame, width=40)
    spool_combo.pack(anchor="w", pady=2)

    tk.Label(frame, text="PAINTING DO NO").pack(anchor="w", pady=(10,0))
    do_entry = tk.Entry(frame, width=40)
    do_entry.pack(anchor="w", pady=(0,5))

    tk.Label(frame, text="DELIVERY DATE (dd/mm/yyyy)").pack(anchor="w", pady=(5,0))
    date_entry = tk.Entry(frame, width=40)
    date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))
    date_entry.pack(anchor="w", pady=(0,10))

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
        do_entry.delete(0, tk.END)
        date_entry.delete(0, tk.END)
        date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

    def on_line_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        pages = sorted(set(r[2] for r in iso_data if r[0] == iso and r[1] == line))
        page_combo['values'] = pages
        page_combo.set("")
        spool_combo.set("")

    def on_page_select(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spools = sorted(set(r[3] for r in iso_data if r[0] == iso and r[1] == line and r[2] == page))
        spool_combo['values'] = spools
        spool_combo.set("")

    def show_existing_painting(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not (iso and line and page and spool): return

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT delivery_order_no, delivery_date FROM spools
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=?
            """, (iso, line, page, spool))
            r = cur.fetchone()

        if not r: return
        do_no, date_val = r
        do_entry.delete(0, tk.END)
        do_entry.insert(0, do_no or "")
        if date_val:
            try:
                date_disp = datetime.strptime(date_val, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                date_disp = date_val
            date_entry.delete(0, tk.END)
            date_entry.insert(0, date_disp)

    def save_painting():
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        do_no = do_entry.get().strip()
        date_str = date_entry.get().strip()

        if not (iso and line and page and spool and do_no and date_str):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            date_sql = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format.")
            return

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE spools SET delivery_order_no=?, delivery_date=?
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=?
            """, (do_no, date_sql, iso, line, page, spool))
            conn.commit()

        messagebox.showinfo("Success", "Painting delivery updated.")

    update_button = tk.Button(frame, text="✅ Update Painting Delivery", command=save_painting)
    update_button.pack(anchor="w", pady=(5,0))

    iso_var.trace_add("write", update_iso_listbox)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    line_combo.bind("<<ComboboxSelected>>", on_line_select)
    page_combo.bind("<<ComboboxSelected>>", on_page_select)
    spool_combo.bind("<<ComboboxSelected>>", show_existing_painting)

    return frame
