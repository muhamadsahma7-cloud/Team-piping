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


def clean_base(url: str) -> str:
    """scheme + host + path only - drop any ?query or #fragment a user may
    have pasted in (e.g. a copied address bar with ?theme=dark)."""
    from urllib.parse import urlsplit, urlunsplit

    u = (url or "").strip()
    if not u:
        return ""
    if "//" not in u:
        u = "https://" + u
    p = urlsplit(u)
    return urlunsplit((p.scheme or "https", p.netloc, p.path.rstrip("/"), "", ""))


def scan_url(base: str, code: str, kiosk_token: str = "") -> str:
    base = clean_base(base)
    q = f"?scan={code}"
    if kiosk_token:
        q += f"&k={kiosk_token}"
    return f"{base}/{q}" if base else q


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


def labels_pdf(rows: list[dict], base_url: str, *, kiosk_token: str = "",
               cols: int = 3, rows_per_page: int = 5) -> bytes:
    """Print-ready sheet of QR labels, one per spool.

    rows: dicts with keys  qr_id, wo, batch, iso, line, page, spool,
                           material, joints
    Returns a multi-page PDF (A4 portrait, ~150 dpi).
    """
    import qrcode
    from PIL import Image, ImageDraw

    PAGE_W, PAGE_H = 1240, 1754                       # A4 @ ~150 dpi
    MARGIN = 40
    cell_w = (PAGE_W - 2 * MARGIN) // cols
    cell_h = (PAGE_H - 2 * MARGIN) // rows_per_page
    per_page = cols * rows_per_page
    f_val = _font(17)
    f_lbl = _font(12)
    f_spool = _font(20)
    LINE_H = 17
    LBL_X = 78                                        # value column offset

    def _clip(s: str, n: int = 30) -> str:
        return s if len(s) <= n else s[:n - 1] + "…"

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

        def _v(key: str) -> str:
            return str(r.get(key) or "").strip() or "—"

        jn = r.get("joints")
        fields = [
            ("ISO", _v("iso")),
            ("SPOOL", _v("spool") + (f"   ({jn} jt)" if jn else "")),
            ("LINE", _v("line")),
            ("PAGE", _v("page")),
            ("AREA", _v("area")),
            ("BATCH", _v("batch")),
            ("WO", _v("wo")),
            ("MATERIAL", _v("material")),
        ]

        qr = qrcode.make(scan_url(base_url, r["qr_id"], kiosk_token),
                         box_size=6, border=1).get_image().convert("RGB")
        q = min(cell_w - 30, cell_h - (len(fields) + 1) * LINE_H - 34)
        qr = qr.resize((q, q))
        page.paste(qr, (cx + (cell_w - q) // 2, cy + 10))
        ty = cy + 10 + q + 8
        for k, (lbl, val) in enumerate(fields):
            yy = ty + k * LINE_H
            draw.text((cx + 12, yy + 2), lbl, fill="#777777", font=f_lbl)
            draw.text((cx + LBL_X, yy), _clip(val, 30),
                      fill="black", font=(f_spool if lbl == "SPOOL" else f_val))
        draw.text((cx + 12, ty + len(fields) * LINE_H + 3), r["qr_id"],
                  fill="#999999", font=f_lbl)

    if not pages:
        pages = [Image.new("RGB", (PAGE_W, PAGE_H), "white")]

    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    return buf.getvalue()
