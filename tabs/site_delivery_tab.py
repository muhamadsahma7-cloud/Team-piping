import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def build_tab(parent, permissions):
    frame = tk.Frame(parent, padx=10, pady=10)

    # ─── Load Data ───
    with sqlite3.connect("database/spool_tracking.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT iso_dwg_no FROM spools")
        all_iso = sorted(row[0] for row in cur.fetchall())
        cur.execute("SELECT iso_dwg_no, line_no, iso_run_no, dwg_spool_no FROM spools")
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

    tk.Label(frame, text="SITE DO NO").pack(anchor="w", pady=(10,0))
    site_do_entry = tk.Entry(frame, width=40)
    site_do_entry.pack(anchor="w", pady=2)

    tk.Label(frame, text="SITE DELIVERY DATE (dd/mm/yyyy)").pack(anchor="w", pady=(10,0))
    site_date_entry = tk.Entry(frame, width=40)
    site_date_entry.pack(anchor="w", pady=2)
    site_date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

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
        site_do_entry.delete(0, tk.END)
        site_date_entry.delete(0, tk.END)
        site_date_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))

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

    def show_existing_site(event):
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        if not (iso and line and page and spool): return

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT site_do_no, site_delivery_date FROM spools
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=?
            """, (iso, line, page, spool))
            result = cur.fetchone()

        site_do_entry.delete(0, tk.END)
        site_date_entry.delete(0, tk.END)
        if result:
            site_do, site_date = result
            site_do_entry.insert(0, site_do or "")
            if site_date:
                try:
                    formatted = datetime.strptime(site_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                    site_date_entry.insert(0, formatted)
                except:
                    site_date_entry.insert(0, site_date)

    def save_site():
        iso = iso_var.get().strip()
        line = line_combo.get().strip()
        page = page_combo.get().strip()
        spool = spool_combo.get().strip()
        site_do = site_do_entry.get().strip()
        date_str = site_date_entry.get().strip()

        if not (iso and line and page and spool and date_str):
            messagebox.showerror("Error", "Please complete all fields.")
            return

        try:
            site_date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Invalid date format.")
            return

        with sqlite3.connect("database/spool_tracking.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE spools SET site_do_no=?, site_delivery_date=?
                WHERE iso_dwg_no=? AND line_no=? AND iso_run_no=? AND dwg_spool_no=?
            """, (site_do, site_date, iso, line, page, spool))
            conn.commit()

        messagebox.showinfo("Success", "Site Delivery info updated.")

    # ─── Bindings ───
    iso_var.trace_add("write", update_iso_listbox)
    iso_listbox.bind("<<ListboxSelect>>", on_iso_select)
    line_combo.bind("<<ComboboxSelected>>", on_line_select)
    page_combo.bind("<<ComboboxSelected>>", on_page_select)
    spool_combo.bind("<<ComboboxSelected>>", show_existing_site)

    # ─── Save Button ───
    tk.Button(frame, text="✅ Update Site Delivery", command=save_site, width=30).pack(anchor="w", pady=10)

    return frame
