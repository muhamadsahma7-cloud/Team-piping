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


LABEL_W_CM, LABEL_H_CM = 8.5, 5.2                     # landscape sticker / border


def labels_pdf(rows: list[dict], base_url: str, *, kiosk_token: str = "") -> bytes:
    """Print-ready sheet of QR labels, one per spool.

    Landscape label: description on the left, QR on the right. Each
    bordered label is LABEL_W_CM x LABEL_H_CM; cut on the line.

    rows: dicts with keys  qr_id, wo, batch, iso, line, page, area,
                           spool, material, joints
    Returns a multi-page PDF (A4 portrait, ~150 dpi).
    """
    import qrcode
    from PIL import Image, ImageDraw

    DPI = 150
    PAGE_W, PAGE_H = 1240, 1754                       # A4 @ ~150 dpi
    MARGIN = 34
    cell_w = round(LABEL_W_CM / 2.54 * DPI)           # 8.5 cm
    cell_h = round(LABEL_H_CM / 2.54 * DPI)           # 5.2 cm
    cols = max(1, (PAGE_W - 2 * MARGIN) // cell_w)
    rows_per_page = max(1, (PAGE_H - 2 * MARGIN) // cell_h)
    per_page = cols * rows_per_page
    f_val = _font(17)
    f_lbl = _font(12)
    f_spool = _font(19)
    f_code = _font(12)
    PAD = 12

    def _clip(s: str, n: int) -> str:
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

        # border exactly on the cut line
        draw.rectangle([cx, cy, cx + cell_w - 1, cy + cell_h - 1],
                       outline="#999999", width=1)

        def _v(key: str) -> str:
            return str(r.get(key) or "").strip() or "—"

        jn = r.get("joints")
        fields = [
            ("ISO", _v("iso")),
            ("SPOOL", _v("spool") + (f"  ({jn} jt)" if jn else "")),
            ("LINE", _v("line")),
            ("PAGE", _v("page")),
            ("AREA", _v("area")),
            ("BATCH", _v("batch")),
            ("WO", _v("wo")),
            ("MATERIAL", _v("material")),
        ]

        # ---- QR on the right, vertically centred ----
        q = min(cell_h - 2 * PAD, 196)
        qr = qrcode.make(scan_url(base_url, r["qr_id"], kiosk_token),
                         box_size=6, border=1).get_image().convert("RGB")
        qr = qr.resize((q, q))
        qx = cx + cell_w - PAD - q
        page.paste(qr, (qx, cy + (cell_h - q) // 2))
        draw.line([(qx - PAD, cy + 6), (qx - PAD, cy + cell_h - 6)],
                  fill="#dddddd", width=1)

        # ---- description on the left ----
        x0 = cx + PAD
        val_x = x0 + 60
        val_w = qx - PAD - val_x
        vchars = max(8, val_w // 8)
        LINE_H = 24
        block_h = LINE_H * (len(fields) + 1)
        ty = cy + max(PAD, (cell_h - block_h) // 2)
        for k, (lbl, val) in enumerate(fields):
            yy = ty + k * LINE_H
            draw.text((x0, yy + 3), lbl, fill="#777777", font=f_lbl)
            draw.text((val_x, yy), _clip(val, vchars), fill="black",
                      font=(f_spool if lbl == "SPOOL" else f_val))
        draw.text((x0, ty + len(fields) * LINE_H + 2), r["qr_id"],
                  fill="#999999", font=f_code)

    if not pages:
        pages = [Image.new("RGB", (PAGE_W, PAGE_H), "white")]

    buf = io.BytesIO()
    # resolution=DPI so the page prints as true A4 and the border comes
    # out at the real 5.2 x 8.5 cm (print at 100% / "actual size")
    pages[0].save(buf, format="PDF", resolution=DPI, save_all=True,
                  append_images=pages[1:])
    return buf.getvalue()
