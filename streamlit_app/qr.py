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


LABEL_W_CM, LABEL_H_CM = 8.0, 5.2                     # landscape sticker / border

_last_pages: list = []                                # last render, for previews


def _text_h(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text or "X", font=font)
    return b[3] - b[1]


def _txt(draw, xy, text, font, fill="black") -> None:
    draw.text(xy, text, font=font, fill=fill)


def labels_pdf(rows: list[dict], base_url: str, *, kiosk_token: str = "") -> bytes:
    """One QR sticker per PDF page, LABEL_W_CM x LABEL_H_CM landscape, for a
    label / sticker printer. Print at 100% / actual size.

    Layout (matches the shop's paper form):
        +--------------------------------------------------+
        | <ISO drawing no>  (title bar)                    |
        +---------------------+----------------------------+
      W | Spool No. | value   |                            |
      O | Area      | value   |         [  QR  ]           |
        | Service   | value   |                            |
        | Pipe size | value   |                            |
        | Run/Iso No| value   |                            |
        | Paint Code| value   |          <code>            |
        +---------------------+----------------------------+
      (WO-... printed vertically up the left edge)

    rows: dicts with keys  qr_id, iso, spool, area, service, size, page,
                           paint, wo, batch
    """
    import qrcode
    from PIL import Image, ImageDraw

    DPI = 300                                         # high-res raster -> sharp
    S = DPI / 150                                     # design units are @150
    px = lambda v: round(v * S)
    W = round(LABEL_W_CM / 2.54 * DPI)
    H = round(LABEL_H_CM / 2.54 * DPI)

    f_lbl = _font(px(13))
    f_val = _font(px(16))
    f_val_sm = _font(px(13))
    f_wo = _font(px(13))
    f_code = _font(px(16))
    f_titles = [_font(px(s)) for s in (28, 25, 22, 19, 16, 14)]

    STRIP = px(22)                                    # vertical WO column
    TITLE_H = px(44)
    LBL_W = px(100)                                   # label column width
    GAP = px(8)
    BW, HW = px(2), max(1, px(1))                     # heavy / hair line widths

    def _clip(s: str, n: int) -> str:
        return s if len(s) <= n else s[:n - 1] + "…"

    pages: list[Image.Image] = []
    for r in rows:
        def _v(key: str) -> str:
            return str(r.get(key) or "").strip() or "-"

        page = Image.new("RGB", (W, H), "white")
        pages.append(page)
        d = ImageDraw.Draw(page)

        d.rectangle([0, 0, W - 1, H - 1], outline="black", width=BW)

        # ---- vertical WO strip, left edge (WO number only) ----
        wo = _v("wo")
        wo_txt = "WO-" + wo if wo != "-" else "WO -"
        st_img = Image.new("RGB", (H - px(12), STRIP - px(2)), "white")
        _txt(ImageDraw.Draw(st_img), (px(2), 0), wo_txt, f_wo)
        page.paste(st_img.rotate(90, expand=True), (px(2), px(6)))
        d.line([(STRIP, BW), (STRIP, H - BW)], fill="black", width=HW)

        x0 = STRIP
        inner_w = W - x0

        # ---- title bar (ISO drawing no) ----
        d.rectangle([x0, BW, W - BW, BW + TITLE_H], outline="black", width=BW)
        title = _v("iso")
        tf = next((f for f in f_titles
                   if d.textlength(title, font=f) <= inner_w - px(18)), f_titles[-1])
        _txt(d, (x0 + (inner_w - d.textlength(title, font=tf)) / 2,
                 BW + (TITLE_H - _text_h(d, title, tf)) / 2 - px(2)),
             title, tf)

        body_y0 = BW + TITLE_H
        # ---- QR box, right ----
        qx0 = x0 + int(inner_w * 0.52)
        d.rectangle([qx0, body_y0, W - BW, H - BW], outline="black", width=BW)
        code = str(r.get("qr_id", ""))
        code_h = _text_h(d, code, f_code) + px(16)    # reserved strip at the bottom
        box_w, box_h = W - BW - qx0, H - BW - body_y0
        q = min(box_w - px(14), box_h - code_h - px(10))
        raw = (qrcode.make(scan_url(base_url, r["qr_id"], kiosk_token), border=2)
               .get_image().convert("L"))
        scale = max(1, q // raw.width)                # crisp integer upscale
        qimg = raw.resize((raw.width * scale, raw.width * scale), Image.NEAREST)
        qw = qimg.width
        page.paste(qimg, (qx0 + (box_w - qw) // 2,
                          body_y0 + max(px(6), (box_h - code_h - qw) // 2)))
        _txt(d, (qx0 + (box_w - d.textlength(code, font=f_code)) / 2,
                 H - BW - code_h + (code_h - _text_h(d, code, f_code)) / 2 - px(4)),
             code, f_code, fill="#444444")

        # ---- field table, left ----
        fields = [
            ("Spool No.", _v("spool")),
            ("Area", _v("area")),
            ("Service", _v("service")),
            ("Pipe size", _v("size")),
            ("Run / Iso No", _v("page")),
            ("Batch No.", _v("batch")),
            ("Paint Code", _v("paint")),
        ]
        d.rectangle([x0, body_y0, qx0, H - BW], outline="black", width=BW)
        d.line([(x0 + LBL_W, body_y0), (x0 + LBL_W, H - BW)],
               fill="black", width=HW)
        rh = (H - BW - body_y0) / len(fields)
        val_chars = max(6, int((qx0 - x0 - LBL_W - GAP - px(4)) / px(8)))
        for k, (lbl, val) in enumerate(fields):
            yy = body_y0 + k * rh
            if k:
                d.line([(x0, yy), (qx0, yy)], fill="black", width=HW)
            _txt(d, (x0 + px(6), yy + (rh - _text_h(d, lbl, f_lbl)) / 2 - px(1)),
                 lbl, f_lbl)
            vf = f_val if len(val) <= val_chars else f_val_sm
            _txt(d, (x0 + LBL_W + GAP, yy + (rh - _text_h(d, val, vf)) / 2 - px(1)),
                 _clip(val, val_chars + 4), vf)

    if not pages:
        pages = [Image.new("RGB", (W, H), "white")]

    _last_pages.clear()
    _last_pages.extend(pages)                         # for local preview / tests

    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", resolution=DPI, save_all=True,
                  append_images=pages[1:])
    return buf.getvalue()
