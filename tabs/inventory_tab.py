import tkinter as tk
from tkinter import messagebox
import sys
import os
import sqlite3
import pandas as pd
import shutil
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import InventoryManager, FileManager

def build_tab(parent, permissions):
    frame = tk.Frame(parent)

    tk.Label(frame, text="Inventory & Work Order Tools", font=("Arial", 14, "bold")).pack(pady=10)

    def safe_execute(func, success_msg, error_prefix):
        """Safely execute a function and show appropriate messages"""
        try:
            result = func()
            if result:
                messagebox.showinfo("Success", success_msg)
            elif result is False:
                messagebox.showwarning("Warning", "Operation was cancelled or failed.")
        except Exception as e:
            messagebox.showerror("Error", f"{error_prefix}:\n{str(e)}")

    def import_excel_to_db():
        """Import Excel data to database with proper column mapping"""
        from tkinter import filedialog
        import pandas as pd
        import sqlite3
        
        # Select Excel file
        file_path = filedialog.askopenfilename(
            title="Select Excel file to import (Spool Tracking Format)",
            filetypes=[("Excel Files", "*.xlsx"), ("Excel Files", "*.xls")]
        )
        
        if not file_path:
            return False
            
        try:
            # Read Excel file
            df = pd.read_excel(file_path, engine="openpyxl")
            
            # Column mapping from Excel template to database columns
            column_mapping = {
                'WO NO': 'wo_no',
                'ZONE': 'zone',
                'STATUS': 'status',
                'WORKABLE': 'workable',
                'BATCH NO.': 'batch_no',
                'AREA': 'area',
                'LOCATION': 'location',
                'SERVICE': 'service',
                'ISO DWG NO.': 'iso_dwg_no',
                'ISO RUN NO.': 'iso_run_no',
                'REV': 'rev',
                'TEST PACK NO': 'test_pack_no',
                'SYSTEM NO': 'system_no',
                'SUB SYSTEM NO': 'subsystem_no',
                'TEST PRESSURE': 'test_pressure',
                'LINE NO.': 'line_no',
                'LINE SPEC.': 'line_spec',
                'DWG SPOOL NO': 'dwg_spool_no',
                'MATERIAL GROUP': 'material_group',
                'SHOP/FIELD': 'shop_field',
                'JOINT NO': 'joint_no',
                'JOINT SIZE': 'joint_size',
                'SCH': 'schedule',
                'WPS NO': 'wps_no',
                'WELDING PROCESS': 'welding_process',
                'WELDING TYPE': 'welding_type',
                'FIT UP INSPECTION DATE': 'fitup_inspection_date',
                'ITEM 1': 'item_1',
                'SCH / RATING 1': 'sch_rating_1',
                'HEAT NO. 1': 'heat_no_1',
                'ITEM 2': 'item_2',
                'SCH / RATING 2': 'sch_rating_2',
                'HEAT NO. 2': 'heat_no_2',
                'FU REPORT NO': 'fu_report_no',
                'WELDING INSPECTION DATE': 'welding_inspection_date',
                'ROOT WELDER NO': 'root_welder_no',
                'CAPPING WELDER NO': 'capping_welder_no',
                'VISUAL REPORT NO': 'visual_report_no',
                'RT BSR DATE': 'rt_bsr_date',
                'RT BSR REPORT NO': 'rt_bsr_report_no',
                'BSR FRESH JOINT STATUS': 'bsr_fresh_joint_status',
                'TOTAL FILM': 'total_film',
                'FILM ACC': 'film_acc',
                'FILM REJ': 'film_rej',
                'LENGTH REJ': 'length_rej',
                'BSR REPAIR ONE STATUS': 'bsr_repair_one_status',
                'BSR REPAIR TWO STATUS': 'bsr_repair_two_status',
                'PWHT DATE': 'pwht_date',
                'PWHT REPORT NO': 'pwht_report_no',
                'RT ASR DATE': 'rt_asr_date',
                'RT ASR REPORT NO': 'rt_asr_report_no',
                'RT ASR RESULT': 'rt_asr_result',
                'MPI PT DATE': 'mpi_pt_date',
                'MPI PT TYPE': 'mpi_pt_type',
                'MPI PT REPORT NO': 'mpi_pt_report_no',
                'MPI PT RESULT': 'mpi_pt_result',
                'HARDNESS DATE': 'hardness_date',
                'HARNESS REPORT NO': 'hardness_report_no',  # Note: Excel has typo "HARNESS" instead of "HARDNESS"
                'HARDNESS RESULT': 'hardness_result',
                'PMI DATE': 'pmi_date',
                'PMI REPORT NO': 'pmi_report_no',
                'PMI RESULT': 'pmi_result',
                'FERRITE DATE': 'ferrite_date',
                'FERRITE REPORT NO': 'ferrite_report_no',
                'PAINTING DATE': 'painting_date',
                'PAINTING REPORT NO': 'painting_report_no',
                'IRN DATE': 'irn_date',
                'IRN REPORT NO': 'irn_report_no',
                'PAINT SYSTEM': 'paint_system',
                'PWHT': 'pwht',
                'FIT UP DATE': 'fitup_date',
                'WELDING DATE': 'welding_date',
                'PAINTING DO NO': 'delivery_order_no',
                'PAINTING DELIVERY DATE': 'delivery_date',
                'SITE DO NO': 'site_do_no',
                'SITE DELIVERY DATE': 'site_delivery_date',
                'REMARK': 'remark'
            }
            
            # Rename columns to match database schema
            df_mapped = df.rename(columns=column_mapping)
            
            # Keep only columns that exist in the database
            db_columns = list(column_mapping.values())
            df_final = df_mapped[db_columns]
            
            # Connect to database
            conn = sqlite3.connect("database/spool_tracking.db")
            cursor = conn.cursor()
            
            # Get current record count
            cursor.execute("SELECT COUNT(*) FROM spools")
            old_count = cursor.fetchone()[0]
            
            # CLEAR ALL EXISTING DATA FIRST
            cursor.execute("DELETE FROM spools")
            conn.commit()
            
            # Now import the new data (using append since table is now empty)
            df_final.to_sql("spools", conn, if_exists="append", index=False)
            
            # Get new record count
            cursor.execute("SELECT COUNT(*) FROM spools")
            new_count = cursor.fetchone()[0]
            
            conn.close()
            return True
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import Excel file:\n{str(e)}\n\nPlease ensure the file matches the spool tracking template format.")
            return False

    def backup_database():
        """Create backup of the spool tracking database"""
        try:
            # Create backups directory if it doesn't exist
            backup_dir = "database/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_db = "database/spool_tracking.db"
            backup_filename = f"spool_tracking_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Check if source database exists
            if not os.path.exists(source_db):
                messagebox.showerror("Error", "Database file not found!")
                return False
            
            # Copy database file
            shutil.copy2(source_db, backup_path)
            
            # Show success message with backup location
            messagebox.showinfo("Backup Success", 
                f"Database backup created successfully!\n\nBackup saved to:\n{backup_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create database backup:\n{str(e)}")
            return False

    def safe_execute_with_counts(func, success_msg, error_prefix):
        """Execute function and show detailed success message with record counts"""
        try:
            result = func()
            if result:
                # Get the counts from the function execution
                conn = sqlite3.connect("database/spool_tracking.db")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM spools")
                current_count = cursor.fetchone()[0]
                conn.close()
                
                messagebox.showinfo("Success", f"Database completely replaced with new data!\\n\\nNew record count: {current_count}")
            elif result is False:
                messagebox.showwarning("Warning", "Operation was cancelled or failed.")
        except Exception as e:
            messagebox.showerror("Error", f"{error_prefix}:\\n{str(e)}")

    # Button definitions with their corresponding functions
    buttons = [
        ("📥 Import Excel to DB", import_excel_to_db, "Excel data imported to database successfully!", "Error importing Excel to database"),
        ("💾 Backup Database", backup_database, "Database backup created successfully!", "Error creating database backup"),
    ]

    for label, func, success_msg, error_prefix in buttons:
        # Use appropriate handler based on function
        if func == backup_database:
            handler = lambda f=func, s=success_msg, e=error_prefix: safe_execute(f, s, e)
        else:
            handler = lambda f=func, s=success_msg, e=error_prefix: safe_execute_with_counts(f, s, e)
            
        tk.Button(
            frame, 
            text=label, 
            width=40, 
            font=("Arial", 10),
            bg="#3498DB",
            fg="white",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=handler
        ).pack(pady=4)

    return frame
