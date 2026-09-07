# tabs/iso_drawing_tab.py

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import subprocess

UPLOAD_FOLDER = "iso_drawings"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def build_tab(parent, permissions):
    frame = ttk.Frame(parent)

    # ─── Layout Frames ───
    left_frame = tk.Frame(frame, width=300)
    left_frame.pack(side="left", fill="y", padx=10, pady=10)

    right_frame = tk.Frame(frame)
    right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # ─── Search Section ───
    tk.Label(left_frame, text="Search Drawing (ISO No. / REV / Sheet):").pack()
    entry = tk.Entry(left_frame, width=40)
    entry.pack(pady=5)

    # ─── Buttons ───
    tk.Button(left_frame, text="🔍 Search", command=lambda: search_drawings(entry, listbox), width=30).pack(pady=2)
    tk.Button(left_frame, text="📤 Upload Drawing(s)", command=upload_multiple_pdfs, width=30).pack(pady=2)
    tk.Button(left_frame, text="➕ Zoom In", command=lambda: zoom(1.1, listbox, canvas), width=30).pack(pady=2)
    tk.Button(left_frame, text="➖ Zoom Out", command=lambda: zoom(0.9, listbox, canvas), width=30).pack(pady=2)
    tk.Button(left_frame, text="🖐️ Pan Mode (Toggle)", command=toggle_pan, width=30).pack(pady=2)
    tk.Button(left_frame, text="🖨️ Open in External Viewer", command=lambda: open_external(listbox), width=30).pack(pady=2)

    # ─── File List ───
    global matches
    matches = []
    global listbox
    listbox = tk.Listbox(left_frame, width=40, height=40)
    listbox.pack(side="left", fill="both", expand=True, pady=10)

    scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    listbox.bind("<<ListboxSelect>>", lambda e: show_preview(listbox, canvas))

    # ─── Canvas Preview ───
    global canvas, img_tk, current_zoom, pan_mode, last_x, last_y
    canvas = tk.Canvas(right_frame, width=1400, height=900, bg="white", scrollregion=(0, 0, 2000, 2000))
    canvas.pack(fill="both", expand=True)
    canvas.bind("<ButtonPress-1>", start_pan)
    canvas.bind("<B1-Motion>", do_pan)
    current_zoom = 1.0
    pan_mode = False
    last_x = last_y = 0
    img_tk = None

    return frame

# ─── Upload Function ───
def upload_multiple_pdfs():
    filepaths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if not filepaths:
        return

    uploaded = 0
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        dest_path = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.exists(dest_path):
            overwrite = messagebox.askyesno("Overwrite?", f"{filename} already exists. Overwrite?")
            if not overwrite:
                continue

        try:
            shutil.copy(filepath, dest_path)
            uploaded += 1
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload {filename}:\n{e}")

    messagebox.showinfo("Upload Complete", f"{uploaded} file(s) uploaded.")

# ─── Search Function ───
def search_drawings(entry, listbox):
    keyword = entry.get().strip().lower()
    listbox.delete(0, tk.END)
    matches.clear()

    if not keyword:
        messagebox.showwarning("Input Required", "Please enter a keyword (e.g., ISO No. or REV).")
        return

    for file in os.listdir(UPLOAD_FOLDER):
        if file.lower().endswith(".pdf") and keyword in file.lower():
            matches.append(file)
            listbox.insert(tk.END, file)

    if not matches:
        messagebox.showinfo("Not Found", f"No matching drawings found for: {keyword}")

# ─── Preview Function ───
def show_preview(listbox, canvas):
    global img_tk
    sel = listbox.curselection()
    if not sel:
        return

    selected_file = matches[sel[0]]
    filepath = os.path.join(UPLOAD_FOLDER, selected_file)

    try:
        doc = fitz.open(filepath)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=int(100 * current_zoom))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((canvas.winfo_width(), canvas.winfo_height()))
        img_tk = ImageTk.PhotoImage(img)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        doc.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to preview drawing:\n{e}")

# ─── Zoom & Pan ───
def zoom(factor, listbox, canvas):
    global current_zoom
    current_zoom *= factor
    if listbox.curselection():
        show_preview(listbox, canvas)

def toggle_pan():
    global pan_mode
    pan_mode = not pan_mode
    canvas.config(cursor="fleur" if pan_mode else "arrow")

def start_pan(event):
    global last_x, last_y
    if pan_mode:
        last_x = event.x
        last_y = event.y

def do_pan(event):
    global last_x, last_y
    if pan_mode:
        dx = last_x - event.x
        dy = last_y - event.y
        canvas.xview_scroll(dx, "units")
        canvas.yview_scroll(dy, "units")
        last_x = event.x
        last_y = event.y

# ─── External Viewer ───
def open_external(listbox):
    sel = listbox.curselection()
    if not sel:
        return
    selected_file = matches[sel[0]]
    filepath = os.path.join(UPLOAD_FOLDER, selected_file)
    try:
        if os.name == "nt":
            os.startfile(filepath)
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file externally:\n{e}")
