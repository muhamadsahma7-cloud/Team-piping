import sqlite3
import pandas as pd
from datetime import datetime
import os
from openpyxl import load_workbook
import sys
import traceback

# ─── Cuba import tkcalendar ───
use_date_picker = False
try:
    import tkinter as tk
    from tkcalendar import DateEntry
    use_date_picker = True
except ImportError:
    use_date_picker = False

try:
    # ─── Lokasi Asas ───
    cwd = os.path.dirname(sys.executable)
    base_dir = getattr(sys, '_MEIPASS', cwd)

    # ─── Laluan Fail ───
    template_path = os.path.join(cwd, "report template", "DAILY PROGRESS REPORT TEMPLATE R1.xlsx")
    db_path = os.path.join(cwd, "database", "spool_tracking.db")
    output_folder = os.path.join(cwd, "daily_reports")
    os.makedirs(output_folder, exist_ok=True)

    # ─── Pilih Tarikh ───
    if use_date_picker:
        selected_date = [None]  # gunakan list untuk mutable reference

        def pick_date():
            root = tk.Tk()
            root.title("Pilih Tarikh Laporan")
            tk.Label(root, text="Pilih tarikh laporan:").pack(pady=5)
            cal = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            cal.pack(pady=5)

            def confirm():
                selected_date[0] = cal.get_date()
                root.destroy()

            tk.Button(root, text="OK", command=confirm).pack(pady=5)
            root.mainloop()

        pick_date()
        report_date = pd.to_datetime(selected_date[0])
    else:
        input_date = input("Masukkan tarikh laporan (YYYY-MM-DD): ")
        report_date = pd.to_datetime(input_date, errors='coerce')
        if pd.isna(report_date):
            report_date = pd.to_datetime(datetime.today().strftime("%Y-%m-%d"))

    # ─── Load Data ───
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM spools", conn)
    conn.close()

    # ─── Format & Filter ───
    df["joint_size"] = pd.to_numeric(df["joint_size"], errors="coerce")
    df["fitup_date"] = pd.to_datetime(df["fitup_date"], errors="coerce")
    df["welding_date"] = pd.to_datetime(df["welding_date"], errors="coerce")
    df = df[df["shop_field"].astype(str).str.upper() == "S"]

    # ─── Load Template ───
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    wb = load_workbook(template_path)
    ws = wb.active
    
    # Helper function to safely write to cells (handle merged cells)
    def safe_write_cell(worksheet, cell_ref, value):
        try:
            worksheet[cell_ref] = value
        except AttributeError:
            # Handle merged cells - try to write to the top-left cell of the merged range
            try:
                from openpyxl.utils import coordinate_to_tuple
                row, col = coordinate_to_tuple(cell_ref)
                cell = worksheet.cell(row=row, column=col)
                if hasattr(cell, 'value'):
                    cell.value = value
            except:
                pass  # Skip if can't write to this cell

    # ─── Tulis Berdasarkan ZONE ───
    row = 14
    grouped = df.groupby("zone")
    for zone, group_df in grouped:
        area = group_df["area"].iloc[0] if "area" in group_df.columns else ""
        total = group_df["joint_size"].sum()

        fitup_today = group_df[group_df["fitup_date"] == report_date]["joint_size"].sum()
        fitup_cum = group_df[(group_df["fitup_date"].notna()) & (group_df["fitup_date"] < report_date)]["joint_size"].sum()
        fitup_bal = total - fitup_today - fitup_cum

        weld_today = group_df[group_df["welding_date"] == report_date]["joint_size"].sum()
        weld_cum = group_df[(group_df["welding_date"].notna()) & (group_df["welding_date"] < report_date)]["joint_size"].sum()
        weld_bal = total - weld_today - weld_cum

        safe_write_cell(ws, f"B{row}", area)
        safe_write_cell(ws, f"C{row}", zone)
        safe_write_cell(ws, f"D{row}", round(total, 2))
        safe_write_cell(ws, f"E{row}", round(fitup_today, 2))
        safe_write_cell(ws, f"F{row}", round(fitup_cum, 2))
        safe_write_cell(ws, f"G{row}", round(fitup_bal, 2))
        safe_write_cell(ws, f"J{row}", round(weld_today, 2))
        safe_write_cell(ws, f"K{row}", round(weld_cum, 2))
        safe_write_cell(ws, f"L{row}", round(weld_bal, 2))
        row += 1

    # ─── Tulis Berdasarkan WO No ───
    row = 78
    wo_group = df.groupby("wo_no")
    for wo_no, group in wo_group:
        if pd.isna(wo_no) or str(wo_no).strip() == "":
            continue
        total = group["joint_size"].sum()
        weld_done = group[group["welding_date"].notna()]["joint_size"].sum()
        weld_bal = total - weld_done

        safe_write_cell(ws, f"B{row}", wo_no)
        safe_write_cell(ws, f"C{row}", "")
        safe_write_cell(ws, f"D{row}", round(total, 2))
        safe_write_cell(ws, f"E{row}", round(weld_done, 2))
        safe_write_cell(ws, f"F{row}", round(weld_bal, 2))
        row += 1

    # ─── Tulis Berdasarkan ZONE untuk Joint No mengandungi "A" dan shop_field="S" ───
    row = 38
    df_a_joints = df[(df["joint_no"].astype(str).str.contains("A", na=False)) & (df["shop_field"].astype(str).str.upper() == "S")]
    if not df_a_joints.empty:
        grouped_a = df_a_joints.groupby("zone")
        for zone, group_df in grouped_a:
            area = group_df["area"].iloc[0] if "area" in group_df.columns else ""
            total = group_df["joint_size"].sum()

            fitup_today = group_df[group_df["fitup_date"] == report_date]["joint_size"].sum()
            fitup_cum = group_df[(group_df["fitup_date"].notna()) & (group_df["fitup_date"] < report_date)]["joint_size"].sum()
            fitup_bal = total - fitup_today - fitup_cum

            weld_today = group_df[group_df["welding_date"] == report_date]["joint_size"].sum()
            weld_cum = group_df[(group_df["welding_date"].notna()) & (group_df["welding_date"] < report_date)]["joint_size"].sum()
            weld_bal = total - weld_today - weld_cum

            safe_write_cell(ws, f"B{row}", area)
            safe_write_cell(ws, f"C{row}", zone)
            safe_write_cell(ws, f"D{row}", round(total, 2))
            safe_write_cell(ws, f"E{row}", "NEW")
            safe_write_cell(ws, f"F{row}", round(fitup_today, 2))
            safe_write_cell(ws, f"G{row}", round(fitup_cum, 2))
            safe_write_cell(ws, f"H{row}", round(fitup_bal, 2))
            safe_write_cell(ws, f"I{row}", round(weld_today, 2))
            safe_write_cell(ws, f"J{row}", round(weld_cum, 2))
            safe_write_cell(ws, f"K{row}", round(weld_bal, 2))
            row += 1

    # ─── Simpan Fail Output ───
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_path = os.path.join(output_folder, f"daily_report_{timestamp}.xlsx")
    wb.save(output_path)
    os.startfile(output_path)

except Exception as e:
    with open("error_log.txt", "w") as f:
        f.write(traceback.format_exc())
    raise
