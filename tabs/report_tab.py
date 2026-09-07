import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import time

def build_tab(parent, permissions):
    frame = tk.Frame(parent)

    label = tk.Label(frame, text="Daily Reporting and Export Tools", font=("Segoe UI", 12, "bold"))
    label.pack(pady=10)

    def generate_daily_report():
        """Generate daily report using the exact same logic as standalone script"""
        try:
            # Date picker using simple dialog
            date_str = simpledialog.askstring(
                "Daily Report", 
                "Enter report date (YYYY-MM-DD) or leave blank for today:",
                initialvalue=datetime.today().strftime("%Y-%m-%d")
            )
            if not date_str:
                return
                
            try:
                report_date = pd.to_datetime(date_str)
            except:
                report_date = pd.to_datetime(datetime.today().strftime("%Y-%m-%d"))

            # Load Data - exact same logic as standalone script
            db_path = os.path.join("database", "spool_tracking.db")
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT * FROM spools", conn)
            conn.close()

            # Format & Filter - exact same logic as standalone script
            df["joint_size"] = pd.to_numeric(df["joint_size"], errors="coerce")
            df["fitup_date"] = pd.to_datetime(df["fitup_date"], errors="coerce")
            df["welding_date"] = pd.to_datetime(df["welding_date"], errors="coerce")
            df = df[df["shop_field"].astype(str).str.upper() == "S"]

            # Create output folder
            output_folder = "daily_reports"
            os.makedirs(output_folder, exist_ok=True)

            # Load Template - exact same logic as standalone script
            template_path = os.path.join("report template", "DAILY PROGRESS REPORT TEMPLATE R1.xlsx")
            if not os.path.exists(template_path):
                messagebox.showerror("Error", f"Template not found: {template_path}")
                return
                
            wb = load_workbook(template_path)
            ws = wb.active
            
            # Helper function to safely write to cells (handle merged cells) - exact same as standalone
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

            # Zone data - exact same logic as standalone script (row 14 onwards)
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

            # WO section - exact same logic as standalone script (row 89 onwards)
            row = 89
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

            # Section for joints with "A" in joint_no and shop_field="S" - exact same logic as standalone script (row 49)
            row = 49
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

            # Save file - exact same logic as standalone script
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            output_path = os.path.join(output_folder, f"daily_report_{timestamp}.xlsx")
            wb.save(output_path)
            
            messagebox.showinfo("Success", f"Daily report generated successfully!\nFile: {output_path}")
            
            # Auto-open file
            try:
                os.startfile(os.path.abspath(output_path))
            except:
                pass
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate daily report:\n{str(e)}")

    def classify_spools():
        """Classify spools - maintaining exact original logic"""
        try:
            # Setup - exact same logic
            os.makedirs("classified_spools", exist_ok=True)
            DB_PATH = os.path.join("database", "spool_tracking.db")
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT * FROM spools", conn)
            conn.close()

            # Create Spool Key - exact same logic
            df["spool_key"] = (
                df["line_no"].astype(str).str.strip() + "_" +
                df["iso_dwg_no"].astype(str).str.strip() + "_" +
                df["dwg_spool_no"].astype(str).str.strip() + "_" +
                df["iso_run_no"].astype(str).str.strip()
            )

            # Classification Logic - exact same logic
            status_map = {}
            for spool in df["spool_key"].unique():
                spool_df = df[df["spool_key"] == spool]

                is_straight_pipe = spool_df["dwg_spool_no"].astype(str).str.startswith("SP-SPL").all()
                if not is_straight_pipe:
                    spool_df = spool_df[spool_df["shop_field"] == "S"]
                    if spool_df.empty:
                        continue

                material_group = spool_df["material_group"].astype(str).str.upper().iloc[0]
                pwht_flag = spool_df["pwht"].astype(str).str.upper().iloc[0]
                site_date = spool_df.get("site_delivery_date")
                painting_date = spool_df.get("delivery_date")

                # Date checks - exact same logic
                fitup_filled = spool_df["fitup_date"].notna().all() and spool_df["fitup_date"].ne("").all()
                weld_filled = spool_df["welding_date"].notna().all() and spool_df["welding_date"].ne("").all()
                pwht_filled = "pwht_date" in spool_df.columns and spool_df["pwht_date"].notna().all() and spool_df["pwht_date"].ne("").all()
                fitup_insp_filled = spool_df["fitup_inspection_date"].notna().all() and spool_df["fitup_inspection_date"].ne("").all()
                weld_insp_filled = spool_df["welding_inspection_date"].notna().all() and spool_df["welding_inspection_date"].ne("").all()
                irn_filled = spool_df["irn_date"].notna().all() and spool_df["irn_date"].ne("").all()

                # Status Logic - exact same logic
                if is_straight_pipe:
                    if site_date.notna().any() and site_date.astype(str).str.strip().ne("").any():
                        status = "Sent to Site"
                    elif painting_date.notna().any() and painting_date.astype(str).str.strip().ne("").any():
                        status = "Sent to Painting"
                    else:
                        status = "Ready to Release-Straight Pipe"
                elif site_date.notna().any() and site_date.astype(str).str.strip().ne("").any():
                    status = "Sent to Site"
                elif painting_date.notna().any() and painting_date.astype(str).str.strip().ne("").any():
                    if material_group in ["SS", "SS304", "SS316"]:
                        status = "Sent to Site"
                    else:
                        status = "Sent to Painting"
                elif material_group in ["SS304", "SS_304", "SS316", "SS_316"] and fitup_insp_filled and weld_insp_filled and irn_filled:
                    status = "Ready to Release"
                elif pwht_flag == "YES" and fitup_filled and weld_filled and not pwht_filled:
                    status = "Ready for PWHT"
                elif (pwht_flag == "YES" and fitup_filled and weld_filled and pwht_filled) or (pwht_flag != "YES" and fitup_filled and weld_filled):
                    if not irn_filled:
                        status = "All done-Awaiting IRN"
                    else:
                        status = "Ready to Release"
                elif fitup_insp_filled and weld_insp_filled and irn_filled:
                    status = "Ready to Release"
                elif spool_df["fitup_date"].isnull().all() or spool_df["fitup_date"].eq("").all():
                    status = "Not Started"
                elif spool_df["welding_date"].isnull().any() or spool_df["welding_date"].eq("").any():
                    status = "Under Fabrication"
                else:
                    status = "Under Fabrication"

                status_map[spool] = status

            df["Spool Status"] = df["spool_key"].map(status_map)

            # Data preparation - exact same logic
            df["joint_size"] = pd.to_numeric(df["joint_size"], errors="coerce")
            df_final = df[[ 
                "spool_key", "wo_no", "material_group", "zone", "service", "line_no", "iso_dwg_no",
                "dwg_spool_no", "iso_run_no", "rev", "shop_field", "joint_no",
                "joint_size", "welding_type", "pwht", "fitup_date", "welding_date",
                "fitup_inspection_date", "welding_inspection_date", "irn_date",
                "delivery_date", "site_delivery_date", "paint_system", "Spool Status"
            ]].copy()

            # Filter for summary - exact same logic
            df_shop = df_final[
                (df_final["shop_field"] == "S") |
                df_final["Spool Status"].isin(["Ready to Release-Straight Pipe", "Sent to Site"])
            ]

            # Summary calculations - exact same logic
            status_summary = df_shop.groupby("Spool Status").agg(
                Total_Spools=('spool_key', 'nunique'),
                Total_Joints=('joint_no', 'count'),
                Total_DiaInch=('joint_size', 'sum')
            ).reset_index()

            shop_field_summary = df.groupby("shop_field").agg(
                Total_DiaInch=('joint_size', 'sum')
            ).reset_index()

            pipe_spool_summary = df_shop.drop_duplicates(subset=["spool_key"]).copy()
            pipe_spool_summary = pipe_spool_summary[[ 
                "spool_key", "wo_no", "zone", "material_group", "iso_dwg_no", "line_no", 
                "dwg_spool_no", "iso_run_no", "paint_system", "Spool Status"
            ]]

            # Export Excel - exact same logic
            today_str = datetime.today().strftime("%Y-%m-%d_%H%M")
            path = f"classified_spools/classified_spools_{today_str}.xlsx"
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                status_summary.to_excel(writer, index=False, sheet_name="Summary")
                df_final.to_excel(writer, index=False, sheet_name="All Spools")
                pipe_spool_summary.to_excel(writer, index=False, sheet_name="Pipe Spool Summary")
                shop_field_summary.to_excel(writer, index=False, sheet_name="Shop and Field")
                for status in df_shop["Spool Status"].unique():
                    df_status = df_shop[df_shop["Spool Status"] == status]
                    df_status.to_excel(writer, index=False, sheet_name=status[:31])

            # Format Excel - exact same logic
            wb = load_workbook(path)
            fill_colors = {
                "Ready to Release": "C6EFCE",
                "Ready to Release-Straight Pipe": "D5F5E3",
                "Under Fabrication": "FFEB9C",
                "Sent to Painting": "F4B084",
                "Sent to Site": "D9D2E9",
                "Not Started": "FFC7CE",
                "Ready for PWHT": "A9D0F5",
                "All done-Awaiting IRN": "FADBD8"
            }

            def format_sheet(ws):
                ws.auto_filter.ref = ws.dimensions
                ws.freeze_panes = "A2"
                thin = Side(border_style="thin")
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                    status = row[-1].value if len(row) > 1 else None
                    fill_code = fill_colors.get(status, "FFFFFF")
                    fill = PatternFill(start_color=fill_code, end_color=fill_code, fill_type="solid")
                    for cell in row:
                        cell.fill = fill
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                        cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                for col in ws.columns:
                    max_len = max(len(str(cell.value) or "") for cell in col) + 2
                    ws.column_dimensions[col[0].column_letter].width = max_len

            for sheet in wb.sheetnames:
                if sheet != "Summary":
                    format_sheet(wb[sheet])

            wb.save(path)
            
            messagebox.showinfo("Success", f"Spools classified successfully!\nFile: {path}")
            
            # Auto-open file
            try:
                os.startfile(os.path.abspath(path))
            except:
                pass
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to classify spools:\n{str(e)}")

    def run_export_master():
        """Run export master script"""
        try:
            import export_master
            messagebox.showinfo("Success", "Master file exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export master file:\n{str(e)}")

    btn1 = tk.Button(frame, text="📆 Generate Daily Report", width=40,
                     font=("Arial", 10), bg="#3498DB", fg="white", 
                     relief="flat", bd=0, pady=8, cursor="hand2",
                     command=generate_daily_report)
    btn2 = tk.Button(frame, text="📂 Classify Spools", width=40,
                     font=("Arial", 10), bg="#3498DB", fg="white", 
                     relief="flat", bd=0, pady=8, cursor="hand2",
                     command=classify_spools)
    btn3 = tk.Button(frame, text="📤 Export Master File", width=40,
                     font=("Arial", 10), bg="#27AE60", fg="white", 
                     relief="flat", bd=0, pady=8, cursor="hand2",
                     command=run_export_master)

    btn1.pack(pady=8)
    btn2.pack(pady=8)
    btn3.pack(pady=8)

    return frame
