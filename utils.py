# utils.py - Consolidated utility functions

import os
import sqlite3
import pandas as pd
import subprocess
from datetime import datetime
from tkinter import filedialog, messagebox, Tk

# Database paths
SPOOL_DB = "database/spool_tracking.db"
MATERIAL_DB = "database/material_tracking.db"

class DatabaseManager:
    """Centralized database operations"""
    
    @staticmethod
    def get_connection(db_type="spool"):
        """Get database connection"""
        db_path = SPOOL_DB if db_type == "spool" else MATERIAL_DB
        return sqlite3.connect(db_path)
    
    @staticmethod
    def execute_query(query, db_type="spool", params=None):
        """Execute query and return results"""
        conn = DatabaseManager.get_connection(db_type)
        try:
            if params:
                result = pd.read_sql_query(query, conn, params=params)
            else:
                result = pd.read_sql_query(query, conn)
            return result
        finally:
            conn.close()
    
    @staticmethod
    def execute_update(query, params, db_type="spool"):
        """Execute update/insert query"""
        conn = DatabaseManager.get_connection(db_type)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

class FileManager:
    """File import/export operations"""
    
    @staticmethod
    def select_excel_file():
        """Select Excel file for import"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        root.destroy()
        return file_path
    
    @staticmethod
    def import_to_table(table_name, db_type="material"):
        """Import Excel data to database table"""
        file_path = FileManager.select_excel_file()
        if not file_path:
            return False
        
        try:
            df = pd.read_excel(file_path, engine="openpyxl")
            conn = DatabaseManager.get_connection(db_type)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.close()
            messagebox.showinfo("Success", f"{table_name.upper()} imported successfully.")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import {table_name}:\n{e}")
            return False
    
    @staticmethod
    def export_to_excel(query, filename_prefix, db_type="material", folder="exports"):
        """Export query results to Excel"""
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        export_file = os.path.join(folder, f"{filename_prefix}_{timestamp}.xlsx")
        
        try:
            df = DatabaseManager.execute_query(query, db_type)
            df.to_excel(export_file, index=False)
            
            # Auto-open file
            if os.name == "nt":
                os.startfile(export_file)
            else:
                subprocess.Popen(["xdg-open", export_file])
            
            return export_file
        except Exception as e:
            messagebox.showerror("Export Failed", f"❌ {e}")
            return None

class InventoryManager:
    """Inventory management operations"""
    
    @staticmethod
    def import_bom():
        """Import BOM data"""
        return FileManager.import_to_table("bom", "material")
    
    @staticmethod
    def import_inventory():
        """Import inventory data"""
        return FileManager.import_to_table("inventory", "material")
    
    @staticmethod
    def export_inventory():
        """Export inventory to Excel"""
        return FileManager.export_to_excel(
            "SELECT * FROM inventory", 
            "Inventory_StockList",
            "material",
            "Inventory stock"
        )
    
    @staticmethod
    def match_bom_vs_inventory():
        """Match BOM against inventory and export results"""
        try:
            conn = DatabaseManager.get_connection("material")
            
            # Load data
            bom_df = pd.read_sql_query("SELECT * FROM bom", conn)
            inv_df = pd.read_sql_query("SELECT * FROM inventory", conn)
            conn.close()
            
            # Filter BOM
            bom_df = bom_df[~bom_df["status"].str.lower().isin(["issued", "hold"])]
            
            # Match
            merged = pd.merge(
                bom_df, inv_df,
                on=["material_grade", "part_name", "item_code", "description", "size", "sch_rating"],
                suffixes=("_bom", "_inv"),
                how="left"
            )
            
            merged["shortage"] = merged["quantity_bom"] > merged["quantity_inv"].fillna(0)
            
            # Export
            os.makedirs("exports", exist_ok=True)
            output_path = os.path.join("exports", "bom_vs_inventory_result.xlsx")
            merged.to_excel(output_path, index=False)
            
            if os.name == "nt":
                os.startfile(output_path)
            
            return output_path
        except Exception as e:
            messagebox.showerror("Error", f"Failed to match BOM vs Inventory:\n{e}")
            return None
    
    @staticmethod
    def deduct_inventory(item_code, quantity):
        """Deduct quantity from inventory"""
        query = """
        UPDATE inventory 
        SET quantity_inv = quantity_inv - ? 
        WHERE item_code = ? AND quantity_inv >= ?
        """
        return DatabaseManager.execute_update(query, [quantity, item_code, quantity], "material")
    
    @staticmethod
    def update_inventory_stock(item_code, new_quantity):
        """Update inventory stock level"""
        query = "UPDATE inventory SET quantity_inv = ? WHERE item_code = ?"
        return DatabaseManager.execute_update(query, [new_quantity, item_code], "material")

class ReportManager:
    """Report generation utilities"""
    
    @staticmethod
    def generate_daily_report(date_filter=None):
        """Generate daily progress report"""
        query = """
        SELECT iso_dwg_no, dwg_spool_no, pipe_class, 
               fitup_date, welding_date, painting_date, delivery_date
        FROM spools 
        WHERE shop_field = 'S'
        """
        if date_filter:
            query += f" AND DATE(fitup_date) = '{date_filter}'"
        
        return FileManager.export_to_excel(query, "daily_report", "spool")
    
    @staticmethod
    def classify_spools():
        """Classify spools and export results"""
        query = """
        SELECT iso_dwg_no, dwg_spool_no, pipe_class,
               CASE 
                   WHEN fitup_date IS NOT NULL AND welding_date IS NOT NULL 
                        AND painting_date IS NOT NULL THEN 'Ready for Delivery'
                   WHEN fitup_date IS NOT NULL AND welding_date IS NOT NULL THEN 'Ready for Painting'
                   WHEN fitup_date IS NOT NULL THEN 'Ready for Welding'
                   ELSE 'Pending Fit-Up'
               END as status
        FROM spools WHERE shop_field = 'S'
        """
        return FileManager.export_to_excel(query, "classified_spools", "spool", "classified_spools")

# Convenience functions for backward compatibility
def import_bom():
    return InventoryManager.import_bom()

def import_inventory():
    return InventoryManager.import_inventory()

def export_inventory():
    return InventoryManager.export_inventory()

def match_bom_vs_inventory():
    return InventoryManager.match_bom_vs_inventory()

def generate_daily_report():
    return ReportManager.generate_daily_report()

def classify_spools():
    return ReportManager.classify_spools()