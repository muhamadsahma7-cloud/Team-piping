"""QR helpers for the scan-to-update-progress feature.

The QR label carries a full URL:  {base}/?scan={qr_id}
so a phone's built-in camera opens the app straight at that joint - the
app never has to decode a QR itself (keeps it Streamlit-Cloud safe).
"""

from __future__ import annotations

import io
import secrets

# no ambiguous characters (0/O, 1/I/L)
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_code(n: int = 10) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


def scan_url(base: str, code: str) -> str:
    base = (base or "").strip().rstrip("/")
    return f"{base}/?scan={code}" if base else f"?scan={code}"


def qr_png(data: str, *, box_size: int = 9, border: int = 2) -> bytes:
    """Single QR code as PNG bytes."""
    import qrcode

    img = qrcode.make(data, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _font(size: int):
    from PIL import ImageFont

    try:
        return ImageFont.load_default(size=size)      # Pillow >= 10
    except TypeError:
        return ImageFont.load_default()


def labels_pdf(rows: list[dict], base_url: str, *,
               cols: int = 3, rows_per_page: int = 7) -> bytes:
    """Print-ready sheet of QR labels.

    rows: dicts with keys  qr_id, iso, line, spool, joint, size
    Returns a multi-page PDF (A4 portrait, ~150 dpi).
    """
    import qrcode
    from PIL import Image, ImageDraw

    PAGE_W, PAGE_H = 1240, 1754                       # A4 @ ~150 dpi
    MARGIN = 40
    cell_w = (PAGE_W - 2 * MARGIN) // cols
    cell_h = (PAGE_H - 2 * MARGIN) // rows_per_page
    per_page = cols * rows_per_page
    f_big = _font(21)
    f_small = _font(18)

    pages: list[Image.Image] = []
    page = None
    for i, r in enumerate(rows):
        if i % per_page == 0:
            page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
            pages.append(page)
        draw = ImageDraw.Draw(page)
        slot = i % per_page
        cx = MARGIN + (slot % cols) * cell_w
        cy = MARGIN + (slot // cols) * cell_h

        draw.rectangle([cx + 4, cy + 4, cx + cell_w - 4, cy + cell_h - 4],
                       outline="#cccccc", width=1)

        qr = qrcode.make(scan_url(base_url, r["qr_id"]),
                         box_size=6, border=1).get_image().convert("RGB")
        q = min(cell_w - 24, cell_h - 96)
        qr = qr.resize((q, q))
        page.paste(qr, (cx + (cell_w - q) // 2, cy + 12))

        ty = cy + 12 + q + 6
        line1 = f"{r.get('iso', '')}  {r.get('line', '')}".strip()
        line2 = (f"Spool {r.get('spool', '')}  ·  Jt {r.get('joint', '')}"
                 f"  ·  {r.get('size', '')}\"").strip()
        draw.text((cx + 12, ty), line1[:46], fill="black", font=f_small)
        draw.text((cx + 12, ty + 22), line2[:46], fill="black", font=f_big)
        draw.text((cx + 12, ty + 46), r["qr_id"], fill="#666666", font=f_small)

    if not pages:
        pages = [Image.new("RGB", (PAGE_W, PAGE_H), "white")]

    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    return buf.getvalue()
