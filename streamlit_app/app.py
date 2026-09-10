"""Team Piping - Streamlit frontend (verification scaffold).

This is intentionally small: enough to prove the Supabase database is
live, migrated, and queryable. The full tab port (fit-up / welding /
NDT / RT / PWHT / IRN / manpower reports, etc.) comes later.

Run:
    pip install -r streamlit_app/requirements.txt
    # create streamlit_app/.streamlit/secrets.toml from the .example
    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import base64
import html
import math
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

MYT = ZoneInfo("Asia/Kuala_Lumpur")

import altair as alt
import pandas as pd
import streamlit as st

import db
import qr
import reports

_LOGO_PATH = Path(__file__).parent / "assets" / "naec_logo.jpg"
try:
    LOGO_URI = "data:image/jpeg;base64," + base64.b64encode(
        _LOGO_PATH.read_bytes()).decode()
except Exception:
    LOGO_URI = ""

_PCT = dict(min_value=0, max_value=100, format="%.0f%%")


def num2_cfg(df: pd.DataFrame) -> dict:
    """column_config that renders every float column at 2 decimals."""
    return {c: st.column_config.NumberColumn(c, format="%.2f")
            for c in df.columns if pd.api.types.is_float_dtype(df[c])}


def show_table(df: pd.DataFrame, name: str, *, progress: tuple = (),
               money: tuple = (), styler=None, height: int | None = None,
               dp2: bool = True) -> None:
    """A dataframe with 2-dp numbers, optional progress columns, and a CSV download."""
    cfg = {c: st.column_config.ProgressColumn(c.replace("_", " "), **_PCT)
           for c in progress if c in df.columns}
    if dp2:
        for c in df.columns:
            if c in cfg or c in money:
                continue
            if pd.api.types.is_float_dtype(df[c]):
                cfg[c] = st.column_config.NumberColumn(c.replace("_", " "), format="%.2f")
    cfg.update({c: st.column_config.NumberColumn(c.replace("_", " "), format="%.2f")
                for c in money if c in df.columns})
    kw = {"height": height} if height is not None else {}
    st.dataframe(styler if styler is not None else df, use_container_width=True,
                 hide_index=True, column_config=cfg, **kw)
    st.download_button("⬇ CSV", df.to_csv(index=False).encode(),
                       file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}")


def is_dark() -> bool:
    """Active theme. In-app toggle (theme_choice / ?theme=) wins; else the
    viewer's Streamlit theme; else light."""
    c = st.session_state.get("theme_choice")
    if c is None:
        qp = st.query_params.get("theme")
        if qp in ("light", "dark"):
            c = st.session_state["theme_choice"] = qp
    if c in ("light", "dark"):
        return c == "dark"
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def dark_alt(chart):
    """Theme-aware Altair config (call once, at render)."""
    d = is_dark()
    axis = "#9fb0c9" if d else "#5b6b80"
    grid = "#26344c" if d else "#e3e8ef"
    return (
        chart.configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=axis, titleColor=axis, gridColor=grid, domainColor=grid)
        .configure_legend(labelColor=axis, titleColor=axis)
        .configure_title(color="#e2e8f0" if d else "#1f2933")
    )


def donut(done: float, total: float, color: str = "#22c55e"):
    d = is_dark()
    pct = (done / total * 100) if total else 0
    src = pd.DataFrame({"cat": ["done", "remaining"],
                        "val": [done, max(total - done, 0.0)]})
    arc = (
        alt.Chart(src).mark_arc(innerRadius=48, outerRadius=72)
        .encode(theta=alt.Theta("val:Q", stack=True),
                color=alt.Color("cat:N", legend=None,
                                scale=alt.Scale(domain=["done", "remaining"],
                                                range=[color, "#2b3a52" if d else "#e5e9f0"])),
                tooltip=[alt.Tooltip("cat:N", title=""),
                         alt.Tooltip("val:Q", title="dia-inch", format=",.1f")])
    )
    text = (alt.Chart(pd.DataFrame({"t": [f"{pct:.0f}%"]}))
            .mark_text(size=22, fontWeight="bold",
                       color="#e2e8f0" if d else "#1f2933").encode(text="t:N"))
    return (arc + text).properties(height=180)


def donut_block(col, label: str, done: float, total: float, color: str) -> None:
    col.markdown(
        f"<div style='text-align:center;line-height:1.25'>"
        f"<b>{label}</b><br>"
        f"<span style='color:var(--muted,#94a3b8);font-size:0.85em'>"
        f"{done:,.0f} / {total:,.0f} dia-inch</span></div>",
        unsafe_allow_html=True,
    )
    col.altair_chart(dark_alt(donut(done, total, color)), use_container_width=True)

st.set_page_config(
    page_title="Team Piping — NAEC Malaysia",
    page_icon=str(_LOGO_PATH) if _LOGO_PATH.exists() else "🛠️",
    layout="wide",
)

# piping-routing mark: a pipe run with two elbows + flanged ends
_PIPE_SVG = (
    "<svg width='32' height='32' viewBox='0 0 32 32' "
    "style='vertical-align:-7px;margin-right:7px'>"
    "<path d='M2 9h9a4 4 0 0 1 4 4v6a4 4 0 0 0 4 4h9' fill='none' "
    "stroke='#4d8dff' stroke-width='3.4' stroke-linecap='round'/>"
    "<circle cx='2' cy='9' r='2.9' fill='#f59f00'/>"
    "<circle cx='30' cy='23' r='2.9' fill='#f59f00'/></svg>"
)
BRAND_HTML = (
    "<div style='line-height:1.12;margin:.1rem 0 .35rem'>"
    f"<div style='font-size:1.7rem;font-weight:800;color:var(--ink,#f1f5f9)'>"
    f"{_PIPE_SVG}Team Piping</div>"
    "<div style='font-size:.72rem;font-weight:700;letter-spacing:.16em;"
    "color:var(--accent,#4d8dff);margin-top:3px'>NAEC MALAYSIA SDN BHD</div></div>"
)

PAGE_ICONS = {
    "Overview": "📊", "Targets & plan": "🎯", "Work order summary": "📋",
    "Update progress": "✏️", "Scan & update": "📲", "Field workers": "🦺",
    "QR labels": "🏷️", "Delivery": "🚚", "Spools": "🔩",
    "Classify & export": "🗂️", "QC WCS": "🧾", "Inventory": "📦", "Manpower": "👷",
    "Activity": "📜", "Data admin": "🛠️", "Users": "👥",
}


_TOK_DARK = {
    "accent": "#4d8dff", "accent2": "#22c55e", "ink": "#f1f5f9", "text": "#e2e8f0",
    "line": "#2b3a52", "panel": "#1a2436", "muted": "#94a3b8",
    "bg": "#0f172a", "cell": "#111a2e", "cell2": "#0c1424", "hdr": "#182338",
    "hdr2": "#1e2b45",
    "inputbg": "#0f1a2e", "inputbd": "#35507a", "inputtx": "#e6edf7", "inputph": "#7a8db0",
    "sb1": "#152036", "sb2": "#111a2e", "sb3": "#161327",
    "glass": "rgba(255,255,255,.06)", "glassbd": "rgba(255,255,255,.12)",
    "glasshov": "rgba(77,141,255,.18)",
    "pill": "rgba(255,255,255,.045)", "pillbd": "rgba(255,255,255,.08)",
    "pillhov": "rgba(255,255,255,.09)",
    "pillact": "rgba(77,141,255,.20)", "pillactbd": "rgba(77,141,255,.55)",
    "sbshadow": "0 2px 14px rgba(0,0,0,.35)", "pillshadow": "0 1px 8px rgba(0,0,0,.3)",
    "dlshadow": "rgba(77,141,255,.28)",
}
_TOK_LIGHT = {
    "accent": "#2f6feb", "accent2": "#12b886", "ink": "#1f2933", "text": "#1f2933",
    "line": "#e2e8f0", "panel": "#ffffff", "muted": "#5b6b80",
    "bg": "#f6f8fb", "cell": "#ffffff", "cell2": "#f7f9fc", "hdr": "#eef2f7",
    "hdr2": "#e4eaf2",
    "inputbg": "#ffffff", "inputbd": "#cbd5e1", "inputtx": "#1f2933", "inputph": "#94a3b8",
    "sb1": "#eef3fb", "sb2": "#f3f6fc", "sb3": "#f0f2fb",
    "glass": "rgba(255,255,255,.72)", "glassbd": "rgba(15,23,42,.10)",
    "glasshov": "rgba(47,111,235,.10)",
    "pill": "rgba(255,255,255,.62)", "pillbd": "rgba(15,23,42,.08)",
    "pillhov": "rgba(255,255,255,.9)",
    "pillact": "rgba(47,111,235,.12)", "pillactbd": "rgba(47,111,235,.42)",
    "sbshadow": "0 2px 10px rgba(15,23,42,.06)", "pillshadow": "0 1px 6px rgba(15,23,42,.05)",
    "dlshadow": "rgba(47,111,235,.22)",
}

_STATIC_CSS = """
.block-container{padding-top:2rem;max-width:1320px;position:relative;z-index:1}
section[data-testid="stSidebar"]{z-index:2}
.stTextInput input,.stNumberInput input,.stDateInput input,.stTextArea textarea,
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{
  background:var(--inputbg)!important;color:var(--inputtx)!important;
  border:1px solid var(--inputbd)!important;border-radius:8px!important}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:var(--inputph)!important}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:var(--accent)!important}
h1{font-weight:700;letter-spacing:-.01em;color:var(--ink)}
h2{margin-top:.3rem;padding-bottom:.35rem;border-bottom:2px solid var(--line);color:var(--ink)}
h3{color:var(--accent);font-weight:600}
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--sb1) 0%,var(--sb2) 55%,var(--sb3) 100%);
  border-right:1px solid var(--glassbd)}
section[data-testid="stSidebar"] .stButton>button{
  background:var(--glass);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);
  border:1px solid var(--glassbd);box-shadow:var(--sbshadow);border-radius:12px;color:var(--ink)}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:var(--glasshov);border-color:var(--accent);color:var(--accent)}
section[data-testid="stSidebar"] [role="radiogroup"]>label{
  background:var(--pill);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);
  border:1px solid var(--pillbd);box-shadow:var(--pillshadow);border-radius:11px;
  padding:.5rem .7rem!important;margin-bottom:6px;
  transition:background .15s ease,border-color .15s ease,box-shadow .15s ease}
section[data-testid="stSidebar"] [role="radiogroup"]>label:hover{background:var(--pillhov)}
section[data-testid="stSidebar"] [role="radiogroup"]>label:has(input:checked){
  background:var(--pillact);border-color:var(--pillactbd);box-shadow:0 2px 16px var(--pillact)}
section[data-testid="stSidebar"] [role="radiogroup"]>label>div:first-child{display:none}
div[data-testid="stMetric"]{
  background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:12px;padding:14px 16px}
div[data-testid="stMetric"] label p{color:var(--muted);font-weight:500}
[data-testid="stMetric"] label,[data-testid="stMetric"] label *,
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
  max-width:none!important;-webkit-line-clamp:unset!important}
[data-testid="stMetricLabel"] p{font-size:.9rem;font-weight:600;line-height:1.3}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{
  white-space:nowrap!important;overflow:visible!important;color:var(--ink)!important;
  font-size:clamp(1.05rem,1.7vw,1.5rem)!important;font-variant-numeric:tabular-nums}
[data-testid="stMetricDelta"],[data-testid="stMetricDelta"] *{color:var(--muted)!important}
.stButton>button,.stDownloadButton>button,.stForm button{border-radius:9px;font-weight:600}
.stDownloadButton>button{padding:.7rem 1.1rem;font-size:1rem;min-height:3rem}
.stDownloadButton>button[kind="primary"]{box-shadow:0 4px 16px var(--dlshadow)}
div[data-testid="stDataFrame"],div[data-testid="stTable"]{border:1px solid var(--line);border-radius:10px}
.stTabs [data-baseweb="tab-list"]{gap:2px}
.stTabs [aria-selected="true"]{color:var(--accent)!important}
div[data-testid="stAlert"]{border-radius:10px}
[data-testid="stProgress"]>div>div>div{background:var(--accent2)}
hr{margin:1rem 0;border-color:var(--line)}
"""


_FORCE_TMPL = """
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
  background:@bg@!important;color:@text@!important}
[data-testid="stHeader"]{background:transparent!important}
.stMarkdown p,.stMarkdown li,.stMarkdown td,.stMarkdown th,
[data-testid="stWidgetLabel"] p,label p{color:@text@!important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:@muted@!important}
h1,h2,h3,h4{color:@ink@!important}
[data-testid="stExpander"]{background:@panel@!important;border:1px solid @line@!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:@text@!important}
/* Leave st.dataframe (glide-data-grid) fully on Streamlit's own theme.
   Forcing only the background used to leave dark numbers on a dark cell
   when the in-app toggle flipped the page but not Streamlit's theme. */
[data-testid="stDataFrame"] [data-testid="StyledDataFrameDataCell"],
[data-testid="stStyledTable"] td,[data-testid="stTable"] td{color:@text@!important}
"""


def inject_css() -> None:
    dark = is_dark()
    st.session_state["_dark"] = dark
    tok = _TOK_DARK if dark else _TOK_LIGHT
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in tok.items()) + "}"
    force = _FORCE_TMPL
    for k in ("bg", "text", "ink", "panel", "line", "muted", "accent"):
        force = force.replace(f"@{k}@", tok[k])
    st.markdown("<style>" + root + "\n" + _STATIC_CSS + "\n" + force + "</style>",
                unsafe_allow_html=True)
    # faint logo watermark — only once signed in, so it doesn't ghost
    # behind the crisp logo on the login card
    if LOGO_URI and st.session_state.get("user"):
        st.markdown(
            f"""
<style>
.stApp::before {{
  content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background:url("{LOGO_URI}") no-repeat center 45%;
  background-size:min(42vw,460px); opacity:.04; filter:grayscale(1);
}}
</style>
""",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------- login
def login_gate() -> None:
    if st.session_state.get("user"):
        return
    _img = (f"<img src='{LOGO_URI}' alt='NAEC Malaysia' style='display:block;"
            f"width:230px;margin:0 auto 14px;background:#fff;padding:16px 20px;"
            f"border-radius:18px;box-shadow:0 8px 30px rgba(0,0,0,.35)'>"
            if LOGO_URI else "")
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(
            "<style>.stApp::before,.stApp::after{content:none!important;"
            "background:none!important}</style>"
            "<div style='text-align:center'>"
            f"{_img}"
            "<div style='font-size:1.7rem;font-weight:800;color:var(--ink,#f1f5f9);"
            "letter-spacing:.04em'>TEAM PIPING</div>"
            "<div style='font-size:.72rem;font-weight:700;letter-spacing:.16em;"
            "color:var(--accent,#4d8dff);margin-top:3px'>NAEC MALAYSIA SDN BHD</div></div>",
            unsafe_allow_html=True,
        )
        st.subheader("Sign in")
        _projs = db.project_list()
        with st.form("login"):
            proj = (st.selectbox("Project", list(_projs)) if _projs else None)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Sign in", use_container_width=True)
    if ok:
        if _projs:
            st.session_state["conn_name"] = _projs[proj]
            st.session_state["project"] = proj
        perm = db.check_login(u.strip(), p)
        if perm is None:
            st.session_state.pop("conn_name", None)
            st.session_state.pop("project", None)
            st.error("Invalid username or password.")
        else:
            st.cache_data.clear()          # drop any prior project's cached data
            st.session_state["user"] = u.strip()
            st.session_state["permission"] = perm
            st.session_state["just_logged_in"] = True
            try:
                db.log_login(u.strip())
            except Exception:
                pass
            st.rerun()
    st.stop()


def kiosk_auth() -> None:
    """A QR that carries &k=<token> auto-signs-in as the configured
    shop-floor account, so the phone never sees the login screen.
    Set up on the QR labels page; token lives in project_settings."""
    if st.session_state.get("user"):
        return
    k = st.query_params.get("k")
    if not k:
        return
    try:
        s = db.get_settings()
        if not s.get("kiosk_token") or k != s["kiosk_token"] or not s.get("kiosk_user"):
            return
        row = db.query("SELECT permission FROM user_credentials WHERE username = :u",
                       {"u": s["kiosk_user"]}, ttl=0)
    except Exception:
        return
    if row.empty:
        return
    st.session_state["user"] = s["kiosk_user"]
    st.session_state["permission"] = row.iloc[0]["permission"]
    st.session_state["kiosk"] = True


def welcome_splash() -> None:
    """One-shot full-screen weld-in flourish right after a successful login.
    CSS/SVG only — fades itself out, no rerun needed."""
    if not st.session_state.pop("just_logged_in", False):
        return
    who = html.escape(str(st.session_state.get("user", ""))[:40]) or "welder"
    st.markdown(
        """
<div class="tp-welcome">
  <svg viewBox="0 0 220 220" width="150" height="150" aria-hidden="true">
    <defs>
      <linearGradient id="tpwHeat" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#ffd27a"/>
        <stop offset=".7" stop-color="#ff8a1f"/><stop offset="1" stop-color="#ff5a12"/>
      </linearGradient>
    </defs>
    <circle cx="110" cy="110" r="80" fill="none" stroke="#24344f" stroke-width="10"/>
    <circle class="tpw-bead" cx="110" cy="110" r="80" fill="none"
            stroke="url(#tpwHeat)" stroke-width="10" stroke-linecap="round"
            pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"
            transform="rotate(-90 110 110)"/>
    <g class="tpw-torch">
      <circle cx="110" cy="30" r="6" fill="#fff"/>
      <animateTransform attributeName="transform" type="rotate"
        from="0 110 110" to="360 110 110" dur="1s" begin="0.15s" fill="freeze"/>
    </g>
    <g class="tpw-spark" stroke="#00e5ff" stroke-width="3" stroke-linecap="round">
      <line x1="110" y1="110" x2="110" y2="66"/><line x1="110" y1="110" x2="151" y2="69"/>
      <line x1="110" y1="110" x2="154" y2="110"/><line x1="110" y1="110" x2="151" y2="151"/>
      <line x1="110" y1="110" x2="110" y2="154"/><line x1="110" y1="110" x2="69" y2="151"/>
      <line x1="110" y1="110" x2="66" y2="110"/><line x1="110" y1="110" x2="69" y2="69"/>
    </g>
  </svg>
  <div class="tpw-hi">Welcome</div>
  <div class="tpw-name">__WHO__</div>
  <div class="tpw-sub">Access granted &nbsp;·&nbsp; Weld Control System</div>
</div>
<style>
.tp-welcome{position:fixed;inset:0;z-index:2147483000;pointer-events:none;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;
  background:radial-gradient(1200px 720px at 50% 42%,#16233b 0%,#0b1220 72%);
  animation:tpw-out .7s ease-in 2.1s forwards;font-family:var(--f-body,system-ui,sans-serif)}
@keyframes tpw-out{to{opacity:0;visibility:hidden}}
.tpw-bead{animation:tpw-lay 1s ease-out .15s forwards;
  filter:drop-shadow(0 0 6px #ff8a1f88)}
@keyframes tpw-lay{to{stroke-dashoffset:0}}
.tpw-torch circle{filter:drop-shadow(0 0 6px #fff) drop-shadow(0 0 16px #ffb057)}
.tpw-spark{transform-box:fill-box;transform-origin:center;opacity:0;
  animation:tpw-burst .55s ease-out 1s forwards}
@keyframes tpw-burst{0%{opacity:1;transform:scale(.15)}
  70%{opacity:1}100%{opacity:0;transform:scale(1.5)}}
.tpw-hi{font-size:2.4rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:#f1f5f9;opacity:0;transform:translateY(14px);
  animation:tpw-rise .5s ease-out 1.15s forwards}
.tpw-name{font-size:1.15rem;font-weight:700;letter-spacing:.06em;color:#4d8dff;
  text-shadow:0 0 18px #4d8dff66;opacity:0;transform:translateY(12px);
  animation:tpw-rise .5s ease-out 1.35s forwards}
.tpw-sub{font-family:var(--f-mono,ui-monospace,monospace);font-size:.72rem;
  letter-spacing:.22em;text-transform:uppercase;color:#8aa0bd;opacity:0;
  animation:tpw-rise .5s ease-out 1.55s forwards}
@keyframes tpw-rise{to{opacity:1;transform:translateY(0)}}
@media (prefers-reduced-motion:reduce){
  .tp-welcome{animation:tpw-out .35s ease .9s forwards}
  .tp-welcome *{animation:none!important}
  .tpw-bead{stroke-dashoffset:0}.tpw-spark{opacity:0}
  .tpw-hi,.tpw-name,.tpw-sub{opacity:1;transform:none}}
</style>
""".replace("__WHO__", who),
        unsafe_allow_html=True,
    )


def logout_splash() -> None:
    """One-shot 'weld cools / session closed' flourish after sign-out."""
    if not st.session_state.pop("just_logged_out", False):
        return
    reason = st.session_state.pop("logout_reason", "")
    hi = "Timed out" if reason == "idle" else "Signed out"
    sub = ("Inactive for 30 minutes &nbsp;·&nbsp; session closed" if reason == "idle"
           else "Session closed &nbsp;·&nbsp; see you on the next joint")
    st.markdown(
        ("""
<div class="tp-logout">
  <svg viewBox="0 0 220 220" width="150" height="150" aria-hidden="true">
    <defs>
      <linearGradient id="loHeat" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#ff8a1f"/><stop offset=".55" stop-color="#ff5a12"/>
        <stop offset="1" stop-color="#7a3d18"/>
      </linearGradient>
    </defs>
    <circle cx="110" cy="110" r="80" fill="none" stroke="#2a323d" stroke-width="10"/>
    <circle class="lo-bead" cx="110" cy="110" r="80" fill="none"
            stroke="url(#loHeat)" stroke-width="10" stroke-linecap="round"
            pathLength="100" stroke-dasharray="100" stroke-dashoffset="0"
            transform="rotate(-90 110 110)"/>
    <line class="lo-snap" x1="34" y1="110" x2="186" y2="110"
          stroke="#00e5ff" stroke-width="3" stroke-linecap="round"/>
    <circle class="lo-core" cx="110" cy="110" r="5" fill="#4d8dff"/>
  </svg>
  <div class="lo-hi">__HI__</div>
  <div class="lo-sub">__SUB__</div>
</div>
<style>
.tp-logout{position:fixed;inset:0;z-index:2147483000;pointer-events:none;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;
  background:radial-gradient(1200px 720px at 50% 42%,#131c2c 0%,#0b1220 72%);
  animation:lo-out .6s ease 1.75s forwards;font-family:var(--f-body,system-ui,sans-serif)}
@keyframes lo-out{to{opacity:0;visibility:hidden}}
.lo-bead{animation:lo-cool 1s ease-in .1s forwards;
  filter:drop-shadow(0 0 6px #ff8a1f88)}
@keyframes lo-cool{to{stroke-dashoffset:100;opacity:.12;filter:drop-shadow(0 0 0 #0000)}}
.lo-snap{transform-box:fill-box;transform-origin:center;opacity:0;
  animation:lo-zap .4s ease-out .15s forwards}
@keyframes lo-zap{0%{opacity:1;transform:scaleX(1)}100%{opacity:0;transform:scaleX(0)}}
.lo-core{transform-box:fill-box;transform-origin:center;
  filter:drop-shadow(0 0 12px #4d8dff);animation:lo-die .45s ease-in .6s forwards}
@keyframes lo-die{0%{transform:scale(1);opacity:1}100%{transform:scale(0);opacity:0}}
.lo-hi{font-size:2.2rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:#e8edf3;opacity:0;transform:translateY(12px);
  animation:lo-rise .5s ease-out .85s forwards}
.lo-sub{font-family:var(--f-mono,ui-monospace,monospace);font-size:.72rem;
  letter-spacing:.2em;text-transform:uppercase;color:#8aa0bd;opacity:0;
  animation:lo-rise .5s ease-out 1.05s forwards}
@keyframes lo-rise{to{opacity:1;transform:translateY(0)}}
@media (prefers-reduced-motion:reduce){
  .tp-logout{animation:lo-out .35s ease .8s forwards}
  .tp-logout *{animation:none!important}
  .lo-bead{stroke-dashoffset:100;opacity:.12}.lo-snap,.lo-core{opacity:0}
  .lo-hi,.lo-sub{opacity:1;transform:none}}
</style>
""".replace("__HI__", hi).replace("__SUB__", sub)),
        unsafe_allow_html=True,
    )


inject_css()
# A scanned spool QR lands on ?scan=<code>. Streamlit Community Cloud can
# drop the query string while waking the app or through the login rerun,
# so stash it now and heal the URL again once we're past the login gate.
_qs = st.query_params.get("scan")
if _qs and _qs != st.session_state.get("_scan_dismissed"):
    st.session_state["pending_scan"] = _qs
logout_splash()
kiosk_auth()          # QR with &k=<token> signs in silently, before the gate
login_gate()
welcome_splash()

# ---- access control -------------------------------------------------
# Permission tokens recognised by the app. A user's `permission` string in
# user_credentials is a comma-separated list of these (or the literal 'all').
KNOWN_TOKENS = [
    "all", "Spools", "Project Summary", "Targets", "Update Fit-Up", "Update Welding",
    "Painting Delivery", "Site Delivery", "Generate Reports", "Inventory",
    "Manpower Report", "QC WCS", "Field Scan",
]
ADMIN = "__admin__"   # page tokens that only 'all' can satisfy

# page -> tokens that grant it. [] = every signed-in user (read-only views).
# Data-entry and admin pages are gated; the plan/report views stay open.
PAGE_PERMS = {
    "Overview": [],
    "Targets & plan": ["Targets"],
    "Work order summary": [],
    "Update progress": ["Update Fit-Up", "Update Welding"],
    "Scan & update": ["Field Scan", "Update Fit-Up", "Update Welding"],
    "Field workers": [ADMIN],
    "QR labels": [ADMIN],
    "Delivery": ["Painting Delivery", "Site Delivery"],
    "Spools": [],
    "Classify & export": ["Generate Reports"],
    "QC WCS": [],
    "Inventory": ["Inventory"],
    "Manpower": ["Manpower Report"],
    "Activity": [ADMIN],
    "Data admin": [ADMIN],
    "Users": [ADMIN],
}


def can_see(page: str, perm: str) -> bool:
    if perm == "all":
        return True
    have = {t.strip() for t in str(perm or "").split(",") if t.strip()}
    # a pure shop-floor account (only "Field Scan") sees the scan page and
    # nothing else - no read-only tabs, no roster
    if have == {"Field Scan"}:
        return page == "Scan & update"
    toks = PAGE_PERMS.get(page, [])
    if not toks:
        return True
    if ADMIN in toks:
        return False
    return any(t in perm for t in toks)


IDLE_LIMIT_S = 1800   # auto sign-out after 30 min with no interaction


@st.fragment(run_every="1s")
def sidebar_clock() -> None:
    la = st.session_state.get("last_active")
    if la is not None:
        idle = time.time() - la
        if idle >= IDLE_LIMIT_S:
            st.cache_data.clear()
            st.session_state.clear()
            st.session_state["just_logged_out"] = True
            st.session_state["logout_reason"] = "idle"
            try:
                st.rerun(scope="app")
            except TypeError:
                st.rerun()
            return
    now = datetime.now(MYT)
    countdown = ""
    if la is not None and IDLE_LIMIT_S - (time.time() - la) <= 60:
        left = max(0, int(IDLE_LIMIT_S - (time.time() - la)))
        countdown = (f"<br><span style='font-size:11px;color:#e0a83a'>"
                     f"Auto sign-out in {left // 60}:{left % 60:02d}</span>")
    st.markdown(
        "<div style='font-family:ui-monospace,SFMono-Regular,Menlo,monospace;"
        "letter-spacing:.06em;color:#8aa0bd;line-height:1.55;padding:2px 0 4px'>"
        f"{now:%A, %d %b %Y}<br>"
        f"<span style='font-size:18px;font-weight:700;color:#4d8dff'>{now:%H:%M:%S}</span>"
        f" <span style='font-size:11px;color:#6b7a90'>MYT</span>{countdown}</div>",
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.session_state["last_active"] = time.time()   # every real (interaction) rerun
    st.markdown(BRAND_HTML, unsafe_allow_html=True)
    if st.session_state.get("project"):
        st.caption(f"Project: **{st.session_state['project']}**")
    st.caption(f"Signed in as **{st.session_state['user']}**"
               + ("  ·  kiosk" if st.session_state.get("kiosk") else ""))
    if st.button("Sign out", use_container_width=True):
        st.cache_data.clear()
        st.session_state.clear()
        st.session_state["just_logged_out"] = True
        try:                       # drop &k / &scan so a kiosk QR doesn't re-auth
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()
    sidebar_clock()
    st.divider()
    _perm = st.session_state.get("permission", "")
    visible = [p for p in PAGE_PERMS if can_see(p, _perm)] or ["Overview"]

    # A scanned spool QR (?scan=<code>, stashed into pending_scan up top so
    # it survives the login / wake round-trip) pins the nav to Scan &
    # update. Decide this BEFORE the radio so the widget actually shows it
    # selected - then tapping any other tab is a real change and the
    # on_change handler can release the pin.
    _sc = st.session_state.get("pending_scan")
    if _sc and "Scan & update" in visible:
        if st.query_params.get("scan") != _sc:
            st.query_params["scan"] = _sc          # heal URL after login / wake
        st.session_state["nav"] = "Scan & update"

    def _leave_scan() -> None:            # picking a tab drops the pending scan
        st.session_state["_scan_dismissed"] = st.session_state.pop("pending_scan", None)
        for _drop in (lambda: st.query_params.pop("scan", None),
                      lambda: st.query_params.__delitem__("scan")):
            try:
                _drop()
                break
            except Exception:
                pass

    page = st.radio("Page", visible, label_visibility="collapsed", key="nav",
                    on_change=_leave_scan,
                    format_func=lambda p: f"{PAGE_ICONS.get(p, '•')}  {p}")
    st.divider()
    _cur = "Dark" if is_dark() else "Light"
    _pick = st.segmented_control(
        "Appearance", ["Light", "Dark"], default=_cur,
        selection_mode="single", key="theme_seg", label_visibility="collapsed",
    ) or _cur
    _new = _pick.lower()
    # only persist on a real user pick - not the first-load default
    # reconciliation, which would otherwise write ?theme= and rerun on
    # every fresh session (and race with the ?scan= param)
    if _new != ("dark" if is_dark() else "light"):
        st.session_state["theme_choice"] = _new
        st.query_params["theme"] = _new
        st.rerun()

# guard against a stale / disallowed selection
if not can_see(page, st.session_state.get("permission", "")):
    st.warning("You don't have access to that page.")
    st.stop()


# --------------------------------------------------------------- pages
# ':asof' = view the project as it stood at end of that day (YYYY-MM-DD text).
# All date columns are clean ISO strings, so substr(d,1,10) <= :asof is a safe compare.
_ISO = "^[0-9]{4}-[0-9]{2}-[0-9]{2}"
_STATS_SQL = f"""
WITH wo AS (
    SELECT joint_size,
           (fitup_date ~ '{_ISO}'   AND substr(fitup_date,1,10)   <= :asof) AS fu_done,
           (welding_date ~ '{_ISO}' AND substr(welding_date,1,10) <= :asof) AS wd_done
    FROM spools
    WHERE shop_field='S' AND lower(coalesce(status,''))='issued'
      AND upper(trim(coalesce(workable,'')))='Y'
),
fd AS (
    SELECT substr(fitup_date,1,10) AS dt, sum(joint_size) AS d
    FROM spools
    WHERE shop_field='S' AND fitup_date ~ '{_ISO}' AND substr(fitup_date,1,10) <= :asof
    GROUP BY 1
),
wd AS (
    SELECT substr(welding_date,1,10) AS dt, sum(joint_size) AS d
    FROM spools
    WHERE shop_field='S' AND welding_date ~ '{_ISO}' AND substr(welding_date,1,10) <= :asof
    GROUP BY 1
),
sp AS (
    SELECT bool_and(coalesce(welding_date ~ '{_ISO}'
             AND substr(welding_date,1,10) <= :asof, false))              AS welded,
           bool_or(coalesce(site_delivery_date ~ '{_ISO}'
             AND substr(site_delivery_date,1,10) <= :asof, false))        AS delivered,
           bool_or(coalesce(irn_date ~ '{_ISO}'
             AND substr(irn_date,1,10) <= :asof, false))                  AS irn_done,
           bool_or(coalesce(delivery_date ~ '{_ISO}'
             AND substr(delivery_date,1,10) <= :asof, false))             AS to_paint,
           bool_or(upper(trim(coalesce(paint_status,''))) = 'YES')        AS needs_paint
    FROM spools
    WHERE shop_field='S'
    GROUP BY iso_dwg_no, line_no, iso_run_no, dwg_spool_no
)
SELECT
  (SELECT count(*) FROM sp)                          AS total_spools,
  (SELECT count(*) FROM sp WHERE welded)             AS completed_spools,
  (SELECT count(*) FROM sp WHERE delivered)          AS delivered_spools,
  (SELECT count(*) FROM sp WHERE to_paint)           AS painting_spools,
  (SELECT count(*) FROM sp WHERE welded AND NOT irn_done AND needs_paint)      AS wait_irn_paint,
  (SELECT count(*) FROM sp WHERE welded AND NOT irn_done AND NOT needs_paint)  AS wait_irn_site,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S')                       AS shop_di,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='F')                       AS field_di,
  (SELECT count(DISTINCT wo_no) FROM spools
     WHERE shop_field='S' AND lower(coalesce(status,''))='issued'
       AND upper(trim(coalesce(workable,'')))='Y')                                            AS wo_issued,
  (SELECT coalesce(sum(joint_size),0) FROM wo)                                                AS wo_total_di,
  (SELECT coalesce(sum(joint_size),0) FROM wo WHERE fu_done IS NOT TRUE)                       AS wo_fitup_bal,
  (SELECT coalesce(sum(joint_size),0) FROM wo WHERE fu_done)                                  AS wo_fitup_done,
  (SELECT coalesce(sum(joint_size),0) FROM wo WHERE wd_done)                                  AS wo_welding_done,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND fitup_date ~ '{_ISO}'
       AND substr(fitup_date,1,10) <= :asof)                                                  AS fitup_done,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND welding_date ~ '{_ISO}'
       AND substr(welding_date,1,10) <= :asof)                                                AS welding_done,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND substr(fitup_date,1,10) = :asof)                                AS today_fitup,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND substr(welding_date,1,10) = :asof)                              AS today_welding,
  (SELECT avg(d) FROM fd)                                                                     AS avg_fitup_day,
  (SELECT avg(d) FROM wd)                                                                     AS avg_welding_day,
  (SELECT avg(CASE WHEN mr.total_fitters>0 THEN fd.d/mr.total_fitters ELSE 0 END)
     FROM fd LEFT JOIN manpower_reports mr ON fd.dt=mr.date
     WHERE mr.total_fitters IS NOT NULL AND mr.total_fitters>0)                               AS avg_fitup_fitter,
  (SELECT avg(CASE WHEN mr.total_welders>0 THEN wd.d/mr.total_welders ELSE 0 END)
     FROM wd LEFT JOIN manpower_reports mr ON wd.dt=mr.date
     WHERE mr.total_welders IS NOT NULL AND mr.total_welders>0)                               AS avg_welding_welder,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND site_delivery_date ~ '{_ISO}'
       AND substr(site_delivery_date,1,10) <= :asof)                                          AS delivered_di,
  (SELECT coalesce(sum(joint_size),0) FROM spools
     WHERE shop_field='S' AND lower(coalesce(status,''))='hold')                              AS hold_di
"""


def page_overview() -> None:
    st.header("Project dashboard")

    rng = db.query(
        f"""SELECT
              min(substr(fitup_date,1,10)) FILTER (WHERE fitup_date ~ '{_ISO}') AS lo,
              greatest(max(substr(fitup_date,1,10)) FILTER (WHERE fitup_date ~ '{_ISO}'),
                       max(substr(welding_date,1,10)) FILTER (WHERE welding_date ~ '{_ISO}')) AS hi
            FROM spools""",
        ttl=300,
    ).iloc[0]
    lo = pd.to_datetime(rng["lo"]).date() if rng["lo"] else date(2025, 1, 1)
    hi = max(pd.to_datetime(rng["hi"]).date() if rng["hi"] else date.today(), date.today())

    c = st.columns([1, 3])
    asof = c[0].date_input("As of date", value=hi, min_value=lo, max_value=hi,
                           format="YYYY-MM-DD")
    if asof < date.today():
        c[1].info(f"Showing the project as it stood on **{asof.isoformat()}** "
                  f"(recorded activity {lo.isoformat()} → {min(asof, hi).isoformat()}).")

    s = db.query(_STATS_SQL, {"asof": asof.isoformat()}, ttl=30).iloc[0]
    is_today = asof == date.today()
    f = lambda x: f"{float(x or 0):,.2f}"

    shop_di = float(s["shop_di"] or 0)
    wo_welding_bal = float(s["wo_fitup_done"] or 0) - float(s["wo_welding_done"] or 0)
    progress = (float(s["welding_done"] or 0) / shop_di * 100) if shop_di else 0

    fitup_done = float(s["fitup_done"] or 0)
    welding_done = float(s["welding_done"] or 0)
    delivered_di = float(s["delivered_di"] or 0)

    st.subheader("Progress (shop dia-inch)")
    dc = st.columns(3)
    donut_block(dc[0], "Fit-up", fitup_done, shop_di, "#5ea0ff")
    donut_block(dc[1], "Welding", welding_done, shop_di, "#34d399")
    donut_block(dc[2], "Delivery", delivered_di, shop_di, "#fbbf24")
    for label, val in [("Fit-up", fitup_done), ("Welding", welding_done),
                       ("Delivery", delivered_di)]:
        pct = (val / shop_di) if shop_di else 0
        st.progress(min(pct, 1.0),
                    text=f"{label}: {val:,.2f} / {shop_di:,.2f}  ({pct*100:.1f}%)")

    st.subheader("Key figures")
    r1 = st.columns(6)
    r1[0].metric("Total shop dia-inch", f(s["shop_di"]), border=True)
    r1[1].metric("Total field dia-inch", f(s["field_di"]), border=True)
    r1[2].metric("Hold dia-inch", f(s["hold_di"]), border=True,
                 help="Shop joint_size where status = hold.")
    r1[3].metric("Work order issued", f"{int(s['wo_issued'] or 0):,}", border=True)
    r1[4].metric("WO total dia-inch", f(s["wo_total_di"]), border=True)
    r1[5].metric("WO fit-up balance", f(s["wo_fitup_bal"]), border=True)

    day_lbl = "Today's" if is_today else asof.isoformat()
    r2 = st.columns(5)
    r2[0].metric("WO welding balance", f(wo_welding_bal), border=True)
    r2[1].metric(f"{day_lbl} fit-up", f(s["today_fitup"]), border=True)
    r2[2].metric(f"{day_lbl} welding", f(s["today_welding"]), border=True)
    r2[3].metric("Fit-up done", f(s["fitup_done"]), border=True)
    r2[4].metric("Welding done", f(s["welding_done"]), border=True)

    r3 = st.columns(5)
    r3[0].metric("Avg fit-up / day", f(s["avg_fitup_day"]), border=True)
    r3[1].metric("Avg welding / day", f(s["avg_welding_day"]), border=True)
    r3[2].metric("Avg fit-up / fitter", f(s["avg_fitup_fitter"]), border=True)
    r3[3].metric("Avg welding / welder", f(s["avg_welding_welder"]), border=True)
    r3[4].metric("Current progress", f"{progress:.1f}%",
                 delta=f"{progress - 100:.1f}% to target", delta_color="off", border=True)

    tsp = int(s["total_spools"] or 0)
    csp = int(s["completed_spools"] or 0)
    dsp = int(s["delivered_spools"] or 0)
    wip = int(s["wait_irn_paint"] or 0)
    wis = int(s["wait_irn_site"] or 0)
    psp = int(s["painting_spools"] or 0)
    pct = lambda n: (f"{n / tsp * 100:.0f}%" if tsp else None)
    a = st.columns(3)
    a[0].metric("Total pipe spools", f"{tsp:,}", border=True)
    a[1].metric("Total completed spools", f"{csp:,}", pct(csp),
                delta_color="off", border=True)
    a[2].metric("Total spool waiting for QC IRN — painting", f"{wip:,}", pct(wip),
                delta_color="off", border=True,
                help="Welded, needs painting (paint status = Yes), no IRN yet.")
    b = st.columns(3)
    b[0].metric("Total spool waiting for QC IRN — site delivery", f"{wis:,}", pct(wis),
                delta_color="off", border=True,
                help="Welded, no painting required (paint status ≠ Yes), no IRN yet.")
    b[1].metric("Total spools delivered to painting shop", f"{psp:,}", pct(psp),
                delta_color="off", border=True,
                help="Spools with a painting delivery date (delivery_date).")
    b[2].metric("Total spools delivered to site", f"{dsp:,}", pct(dsp),
                delta_color="off", border=True,
                help="Spools with a site delivery date (site_delivery_date).")

    st.subheader("Cumulative S-curve (shop dia-inch)")
    sc = db.query(
        f"""
        SELECT substr(fitup_date,1,10) AS d, sum(joint_size) AS v, 'Fit-up' AS k
        FROM spools WHERE shop_field='S' AND fitup_date ~ '{_ISO}'
          AND substr(fitup_date,1,10) <= :asof GROUP BY 1
        UNION ALL
        SELECT substr(welding_date,1,10) AS d, sum(joint_size) AS v, 'Welding' AS k
        FROM spools WHERE shop_field='S' AND welding_date ~ '{_ISO}'
          AND substr(welding_date,1,10) <= :asof GROUP BY 1
        """,
        {"asof": asof.isoformat()}, ttl=30,
    )
    if sc.empty:
        st.caption("No dated activity yet.")
    else:
        sc["d"] = pd.to_datetime(sc["d"])
        sc["v"] = sc["v"].astype(float)
        sc = sc.sort_values("d")
        sc["Cumulative dia-inch"] = sc.groupby("k")["v"].cumsum()
        st.altair_chart(
            dark_alt(alt.Chart(sc).mark_line(point=True).encode(
                x=alt.X("d:T", title="Date"),
                y=alt.Y("Cumulative dia-inch:Q", title="Cumulative dia-inch"),
                color=alt.Color("k:N", title="Activity",
                                scale=alt.Scale(domain=["Fit-up", "Welding"],
                                                range=["#5ea0ff", "#34d399"])),
                tooltip=[alt.Tooltip("d:T", title="date"), "k:N",
                         alt.Tooltip("Cumulative dia-inch:Q", format=",.1f")],
            ).properties(
                height=300,
                title=alt.TitleParams(
                    f"Cumulative fit-up vs welding — as of {asof.isoformat()}",
                    anchor="start", fontSize=14, fontWeight="bold"),
            )),
            use_container_width=True,
        )

    def breakdown(dim: str) -> pd.DataFrame:
        d = db.query(
            f"""
            SELECT coalesce(nullif(trim({dim}::text),''),'(blank)') AS "{dim}",
                   count(*) AS joints,
                   round(coalesce(sum(joint_size),0),2) AS dia_inch,
                   round(coalesce(sum(joint_size) FILTER (
                       WHERE fitup_date ~ '{_ISO}' AND substr(fitup_date,1,10) <= :asof),0),2) AS fitup_di,
                   round(coalesce(sum(joint_size) FILTER (
                       WHERE welding_date ~ '{_ISO}' AND substr(welding_date,1,10) <= :asof),0),2) AS welding_di
            FROM spools
            WHERE shop_field='S'
            GROUP BY 1 ORDER BY dia_inch DESC
            """,
            {"asof": asof.isoformat()}, ttl=30,
        )
        sp = db.query(
            f"""
            WITH s AS (
                SELECT coalesce(nullif(trim({dim}::text),''),'(blank)') AS k,
                       bool_and(coalesce(welding_date ~ '{_ISO}'
                         AND substr(welding_date,1,10) <= :asof, false)) AS welded
                FROM spools
                WHERE shop_field='S'
                GROUP BY coalesce(nullif(trim({dim}::text),''),'(blank)'),
                         iso_dwg_no, line_no, iso_run_no, dwg_spool_no
            )
            SELECT k AS "{dim}", count(*) AS spools,
                   count(*) FILTER (WHERE welded) AS spool_done
            FROM s GROUP BY 1
            """,
            {"asof": asof.isoformat()}, ttl=30,
        )
        d = d.merge(sp, on=dim, how="left")
        for cc in ("joints", "dia_inch", "fitup_di", "welding_di"):
            d[cc] = d[cc].astype(float)
        for cc in ("spools", "spool_done"):
            d[cc] = d[cc].fillna(0).astype(int)
        di = d["dia_inch"].where(d["dia_inch"] > 0)
        d["fitup_bal"] = (d["dia_inch"] - d["fitup_di"]).round(2)
        d["welding_bal"] = (d["dia_inch"] - d["welding_di"]).round(2)
        d["fitup_%"] = (d["fitup_di"] / di * 100).round(1).fillna(0)
        d["welding_%"] = (d["welding_di"] / di * 100).round(1).fillna(0)
        return d[[dim, "spools", "spool_done", "joints", "dia_inch",
                  "fitup_di", "fitup_bal", "fitup_%",
                  "welding_di", "welding_bal", "welding_%"]]

    _mny = ("dia_inch", "fitup_di", "fitup_bal", "welding_di", "welding_bal")
    st.subheader("Breakdown")
    st.caption("Shop spools only · `spool_done` = every joint welded by the as-of date "
               "(ties to *Total completed spools* above).")
    t1, t2, t3 = st.tabs(["By work order", "By batch no", "By area"])
    with t1:
        show_table(breakdown("wo_no"), "progress_by_wo",
                   progress=("fitup_%", "welding_%"), money=_mny)
    with t2:
        show_table(breakdown("batch_no"), "progress_by_batch",
                   progress=("fitup_%", "welding_%"), money=_mny)
    with t3:
        show_table(breakdown("area"), "progress_by_area",
                   progress=("fitup_%", "welding_%"), money=_mny)


_WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _is_working(d: date, rest: set[int], holidays: set[date]) -> bool:
    return d.weekday() not in rest and d not in holidays


def _wdays(start: date, end: date, rest: set[int], holidays: set[date]) -> int:
    """Working days in [start, end] inclusive, skipping `rest` weekdays and `holidays`."""
    if end < start:
        return 0
    n, d = 0, start
    while d <= end:
        if _is_working(d, rest, holidays):
            n += 1
        d += timedelta(days=1)
    return n


def _add_wdays(start: date, n: int, rest: set[int], holidays: set[date]) -> date:
    """Date that is `n` working days after `start`."""
    d, left = start, n
    while left > 0:
        d += timedelta(days=1)
        if _is_working(d, rest, holidays):
            left -= 1
    return d


def _parse_dates(text: str) -> tuple[set[date], list[str]]:
    good, bad = set(), []
    for line in (text or "").replace(",", "\n").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            good.add(pd.to_datetime(s).date())
        except Exception:
            bad.append(s)
    return good, bad


def page_targets() -> None:
    st.header("Targets & plan")
    perm = st.session_state.get("permission", "")
    can_edit = perm == "all" or "Targets" in perm or "Project Summary" in perm
    cfg = db.get_settings()

    lo_row = db.query(
        f"SELECT min(substr(fitup_date,1,10)) lo FROM spools WHERE fitup_date ~ '{_ISO}'",
        ttl=300,
    ).iloc[0]
    d_start = pd.to_datetime(cfg.get("plan_start") or lo_row["lo"] or date.today()).date()
    d_target = (pd.to_datetime(cfg["target_date"]).date()
                if cfg.get("target_date") else date.today() + timedelta(days=60))
    d_scope = cfg.get("scope", "issued")
    _rr = cfg.get("rest")   # '' = deliberately no rest days; missing = default Sunday
    d_rest = [int(x) for x in _rr.split(",") if x] if _rr is not None else [6]
    d_hol_text = "\n".join(x for x in (cfg.get("holidays") or "").split(",") if x)

    # seed the form widgets from the saved plan the first time this browser
    # session opens the page; keyed widgets then keep their value on every
    # rerun / page switch (previously they reset and looked "unsaved").
    for _k, _v in {"tp_start": d_start, "tp_target": d_target, "tp_scope": d_scope,
                   "tp_rest": d_rest, "tp_hol": d_hol_text}.items():
        st.session_state.setdefault(_k, _v)

    with st.form("plan"):
        c = st.columns(4)
        plan_start = c[0].date_input("Plan start", key="tp_start", format="YYYY-MM-DD")
        target_date = c[1].date_input("Target completion", key="tp_target",
                                      format="YYYY-MM-DD")
        scope = c[2].selectbox(
            "Scope", ["issued", "all"], key="tp_scope",
            format_func=lambda v: "Issued work orders" if v == "issued" else "All shop",
        )
        rest = c[3].multiselect("Weekly rest days", options=list(range(7)),
                                key="tp_rest", format_func=lambda i: _WD[i])
        hol_text = st.text_area(
            "Public holidays (one date per line, YYYY-MM-DD)",
            key="tp_hol", height=120, placeholder="2026-01-01\n2026-05-01",
        )
        if st.form_submit_button("Save plan", type="primary", disabled=not can_edit):
            hol_set, bad = _parse_dates(hol_text)
            if bad:
                st.error(f"Not valid dates, fix and re-save: {', '.join(bad)}")
            elif target_date <= plan_start:
                st.error("Target completion must be a date **after** the plan start.")
            else:
                db.set_settings({
                    "plan_start": plan_start.isoformat(),
                    "target_date": target_date.isoformat(),
                    "scope": scope, "rest": ",".join(map(str, rest)),
                    "holidays": ",".join(sorted(d.isoformat() for d in hol_set)),
                })
                st.cache_data.clear()
                st.success("Plan saved.")
                st.rerun()

    st.caption(
        f"Saved plan: **{cfg.get('plan_start', '—')} → {cfg.get('target_date', '—')}** · "
        f"scope **{cfg.get('scope', '—')}** · "
        f"rest **{cfg.get('rest') or 'none'}** · "
        f"holidays **{cfg.get('holidays') or 'none'}**"
    )
    if not can_edit:
        st.caption("View only — needs the 'Targets & plan' grant (or 'all') to change the plan.")

    rest_s = set(rest)
    hol_s, _ = _parse_dates(hol_text)
    today = date.today()
    scope_where = ("AND lower(coalesce(status,''))='issued' "
                   "AND upper(trim(coalesce(workable,'')))='Y'") if scope == "issued" else ""
    scope_di = float(db.query(
        f"SELECT coalesce(sum(joint_size),0) v FROM spools WHERE shop_field='S' {scope_where}",
        ttl=60,
    ).iloc[0]["v"])

    def series(col: str) -> pd.DataFrame:
        return db.query(
            f"""SELECT substr({col},1,10) AS dt, sum(joint_size) AS di
                FROM spools
                WHERE shop_field='S' AND {col} ~ '{_ISO}' {scope_where}
                GROUP BY 1 ORDER BY 1""",
            ttl=60,
        )

    total_wd = _wdays(plan_start, target_date, rest_s, hol_s)
    elapsed_wd = _wdays(plan_start, min(today, target_date), rest_s, hol_s)
    remain_wd = _wdays(today + timedelta(days=1), target_date, rest_s, hol_s)

    if total_wd <= 0:
        st.error(
            f"No working days between plan start (**{plan_start.isoformat()}**) and "
            f"target completion (**{target_date.isoformat()}**). "
            "The target must be after the plan start — fix the dates above (and check "
            "rest days / holidays), then **Save plan**."
        )
        return
    planned_per_day = scope_di / total_wd

    if target_date < today:
        st.warning(f"Target date {target_date.isoformat()} is in the past — "
                   "'required/day' figures are not meaningful.")
    hol_in_window = sum(1 for d in hol_s if plan_start <= d <= target_date)
    st.caption(f"Scope: **{scope_di:,.2f}** dia-inch · working days total **{total_wd}**, "
               f"elapsed **{elapsed_wd}**, remaining **{remain_wd}** "
               f"(weekly rest: {', '.join(_WD[i] for i in sorted(rest_s)) or 'none'}; "
               f"{hol_in_window} public holiday(s) in window)")

    rows, charts = [], {}
    for name, col in [("Fit-up", "fitup_date"), ("Welding", "welding_date")]:
        sdf = series(col)
        done = float(sdf["di"].sum())
        balance = max(scope_di - done, 0.0)
        planned_to_date = min(planned_per_day * elapsed_wd, scope_di)
        delay = planned_to_date - done
        required_now = balance / remain_wd if remain_wd > 0 else float("nan")
        achieved = done / elapsed_wd if elapsed_wd > 0 else 0.0
        if achieved > 0 and balance > 0:
            proj = _add_wdays(today, math.ceil(balance / achieved), rest_s, hol_s).isoformat()
        elif balance <= 0:
            proj = "done"
        else:
            proj = "—"
        rows.append({
            "Discipline": name,
            "Scope": round(scope_di, 2),
            "Done": round(done, 2),
            "Balance": round(balance, 2),
            "Target/day": round(planned_per_day, 2),
            "Required/day now": None if remain_wd == 0 else round(required_now, 2),
            "Achieved/day": round(achieved, 2),
            "Planned to date": round(planned_to_date, 2),
            "Delay qty": round(delay, 2),
            "Projected finish": proj,
            "Status": "BEHIND" if delay > 0.01 else "on track",
        })
        charts[name] = (sdf, planned_per_day)

    rep = pd.DataFrame(rows)
    _num = [c for c in rep.columns if pd.api.types.is_numeric_dtype(rep[c])]
    st.subheader("Plan vs actual")
    st.dataframe(
        rep.style.map(
            lambda v: "color:#f87171;font-weight:bold" if v == "BEHIND" else "color:#34d399",
            subset=["Status"],
        ),
        use_container_width=True, hide_index=True,
        column_config={c: st.column_config.NumberColumn(c, format="%.2f") for c in _num},
    )
    planned_today = float(rep["Planned to date"].iloc[0])   # same for both disciplines
    st.caption(f"Planned qty as of today ({today.isoformat()}) = "
               f"Target/day × elapsed working days = "
               f"{planned_per_day:,.2f} × {elapsed_wd} = **{planned_today:,.2f}** dia-inch")
    b = st.columns(3)
    b[0].metric("Planned qty as of today (dia-inch)", f"{planned_today:,.2f}", border=True)
    for i, r in rep.iterrows():
        b[i + 1].metric(f"{r['Discipline']} delay qty (dia-inch)",
                        f"{r['Delay qty']:,.2f}", r["Status"],
                        delta_color="inverse", border=True)

    # ---- recovery plan : hold the target date, find the catch-up rate ----
    st.subheader("Recovery plan — hold the target date")
    if not rep["Status"].eq("BEHIND").any():
        st.success(f"On or ahead of plan. Nothing to recover — target "
                   f"{target_date.isoformat()} is achievable at the current pace.")
    elif remain_wd <= 0:
        st.error("Target date has passed — no working days left to recover into. "
                 "Set a new target completion date.")
    else:
        crew = db.query(
            "SELECT total_welders, total_fitters FROM manpower_reports "
            "WHERE coalesce(trim(date),'')<>'' ORDER BY date DESC LIMIT 1", ttl=60,
        )
        cur = {"Fit-up": 0, "Welding": 0}
        if not crew.empty:
            cur["Fit-up"] = int(crew.iloc[0]["total_fitters"] or 0)
            cur["Welding"] = int(crew.iloc[0]["total_welders"] or 0)

        # average output per person per day, from manpower_reports (same basis
        # as the dashboard's "Avg fit-up / fitter" and "Avg welding / welder")
        ph = db.query(
            f"""
            SELECT
              (SELECT avg(CASE WHEN mr.total_fitters>0 THEN fd.d/mr.total_fitters END)
                 FROM (SELECT substr(fitup_date,1,10) dt, sum(joint_size) d FROM spools
                       WHERE shop_field='S' AND fitup_date ~ '{_ISO}' GROUP BY 1) fd
                 JOIN manpower_reports mr ON fd.dt = mr.date
                 WHERE mr.total_fitters > 0)                       AS fit_per_head,
              (SELECT avg(CASE WHEN mr.total_welders>0 THEN wd.d/mr.total_welders END)
                 FROM (SELECT substr(welding_date,1,10) dt, sum(joint_size) d FROM spools
                       WHERE shop_field='S' AND welding_date ~ '{_ISO}' GROUP BY 1) wd
                 JOIN manpower_reports mr ON wd.dt = mr.date
                 WHERE mr.total_welders > 0)                       AS weld_per_head
            """,
            ttl=60,
        ).iloc[0]
        per_head_by = {
            "Fit-up": float(ph["fit_per_head"] or 0),
            "Welding": float(ph["weld_per_head"] or 0),
        }

        rec_rows, headline = [], []
        for r in rep.to_dict("records"):
            disc = r["Discipline"]
            bal = float(r["Balance"])
            rate = bal / remain_wd
            ach = float(r["Achieved/day"])
            uplift = rate / ach if ach > 0 else float("nan")
            crew_now = cur[disc]
            per_head = per_head_by[disc]           # dia-inch / person / day
            crew_need = math.ceil(rate / per_head) if per_head > 0 else None
            rec_rows.append({
                "Discipline": disc,
                "Balance": round(bal, 2),
                "Days left": remain_wd,
                "Recovery rate/day": round(rate, 2),
                "Current rate/day": round(ach, 2),
                "Uplift needed": None if ach == 0 else round(uplift, 2),
                "Dia-inch / person / day": round(per_head, 2) if per_head else None,
                "Crew now": crew_now or None,
                "Crew needed": crew_need,
                "Extra crew": (max(crew_need - crew_now, 0)
                               if (crew_need is not None and crew_now) else None),
            })
            if r["Status"] == "BEHIND":
                if crew_need is not None and crew_now:
                    extra = (f", ~{crew_need} {'fitters' if disc == 'Fit-up' else 'welders'}"
                             f" (+{max(crew_need - crew_now, 0)})")
                elif crew_need is not None:
                    extra = f", ~{crew_need} {'fitters' if disc == 'Fit-up' else 'welders'}"
                else:
                    extra = " (no manpower history — add daily counts to size the crew)"
                headline.append(f"**{disc}** → {rate:,.1f}/day "
                                f"({uplift:.1f}× current){extra}")
        st.markdown(f"To finish by **{target_date.isoformat()}** ({remain_wd} working "
                    f"days left): " + " &nbsp;·&nbsp; ".join(headline))
        rr = pd.DataFrame(rec_rows)
        st.dataframe(
            rr, use_container_width=True, hide_index=True,
            column_config={c: st.column_config.NumberColumn(c, format="%.2f")
                           for c in ("Balance", "Recovery rate/day", "Current rate/day",
                                     "Uplift needed", "Dia-inch / person / day")},
        )
        st.caption("Recovery rate = balance ÷ working days left. "
                   "Crew needed = recovery rate ÷ average dia-inch per person per day "
                   "(from `manpower_reports`, same basis as the dashboard's "
                   "*Avg fit-up / fitter* and *Avg welding / welder*).")

    end = max(target_date, today)
    idx = pd.date_range(plan_start, end, freq="D")
    for name, (sdf, ppd) in charts.items():
        with st.expander(f"{name}: planned vs actual vs recovery"):
            act = (sdf.assign(dt=pd.to_datetime(sdf["dt"])).set_index("dt")["di"]
                   .reindex(idx, fill_value=0).cumsum())
            planned = [min(ppd * _wdays(plan_start, min(x.date(), target_date), rest_s, hol_s),
                           scope_di) for x in idx]
            frame = {"Planned": planned, "Actual": act.values}
            done_n = float(act.get(pd.Timestamp(today), act.iloc[-1] if len(act) else 0.0))
            bal_n = max(scope_di - done_n, 0.0)
            if remain_wd > 0 and bal_n > 0.5 and target_date >= today:
                rr_n = bal_n / remain_wd
                frame["Recovery"] = [
                    None if x.date() < today else
                    scope_di if x.date() > target_date else
                    min(done_n + rr_n * _wdays(today + timedelta(days=1), x.date(),
                                               rest_s, hol_s), scope_di)
                    for x in idx
                ]
            st.line_chart(pd.DataFrame(frame, index=idx))


_WO_TOTALS_SQL = """
SELECT
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S')                                   AS total_db,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='issued')      AS issued,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='issued'
     AND coalesce(trim(fitup_date),'')='')                                                                AS bal_fitup_issued,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='issued'
     AND coalesce(trim(welding_date),'')='')                                                              AS bal_weld_issued,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND upper(trim(coalesce(workable,'')))='Y')   AS workable,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND upper(trim(coalesce(workable,'')))='N')   AS non_workable,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='unissued')    AS unissued,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='hold')        AS hold,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND lower(coalesce(status,''))='os')          AS os
"""

_PROGRESS_SQL = """
SELECT
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND fitup_date = :today)   AS today_fitup,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND welding_date = :today) AS today_weld,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND coalesce(trim(fitup_date),'')<>'')   AS cum_fitup,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S' AND coalesce(trim(welding_date),'')<>'') AS cum_weld,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S')                            AS total_di,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S'
     AND coalesce(trim(fitup_inspection_date),'')<>'')                                            AS fitup_insp,
  (SELECT coalesce(sum(joint_size),0) FROM spools WHERE shop_field='S'
     AND coalesce(trim(welding_inspection_date),'')<>'')                                          AS weld_insp
"""


def page_wo_summary() -> None:
    st.header("Work order summary")

    wo = db.query(
        """
        SELECT coalesce(nullif(trim(wo_no),''),'(blank)') AS "WO No",
               coalesce(material_group,'')                AS "Material Group",
               round(coalesce(sum(joint_size),0),2)       AS "Total Dia Inch",
               round(coalesce(sum(joint_size) FILTER (WHERE coalesce(trim(fitup_date),'')=''),0),2)   AS "Balance Fit-Up",
               round(coalesce(sum(joint_size) FILTER (WHERE coalesce(trim(welding_date),'')=''),0),2) AS "Balance Welding"
        FROM spools
        WHERE shop_field='S' AND lower(coalesce(status,''))='issued'
        GROUP BY 1, 2
        ORDER BY "Balance Welding" DESC, "Balance Fit-Up" DESC
        """,
        ttl=30,
    )
    for cc in ("Total Dia Inch", "Balance Fit-Up", "Balance Welding"):
        wo[cc] = wo[cc].astype(float)
    tot = wo["Total Dia Inch"].where(wo["Total Dia Inch"] > 0)
    wo["Fit-up %"] = ((1 - wo["Balance Fit-Up"] / tot) * 100).round(0).fillna(0)
    wo["Welding %"] = ((1 - wo["Balance Welding"] / tot) * 100).round(0).fillna(0)
    done_mask = (wo["Balance Fit-Up"] == 0) & (wo["Balance Welding"] == 0)
    wo_show = wo.assign(Status=["✅ closed" if x else "🔧 open" for x in done_mask])

    st.subheader("Work order issuance — issued WOs")
    a, b, c, e = st.columns(4)
    a.metric("Work orders", f"{len(wo):,}", border=True)
    b.metric("Closed", f"{int(done_mask.sum()):,}", border=True)
    c.metric("Balance fit-up", f"{wo['Balance Fit-Up'].sum():,.2f}", border=True)
    e.metric("Balance welding", f"{wo['Balance Welding'].sum():,.2f}", border=True)

    only_open = st.toggle("Hide closed work orders", value=False)
    view = wo_show[~done_mask] if only_open else wo_show
    styler = view.style.apply(
        lambda r: (["background-color:rgba(34,197,94,.14)"] if r["Status"] == "✅ closed"
                   else [""]) * len(r),
        axis=1,
    )
    show_table(view, "work_order_issuance", styler=styler,
               progress=("Fit-up %", "Welding %"),
               money=("Total Dia Inch", "Balance Fit-Up", "Balance Welding"))

    # ---- progress summary ----
    p = db.query(_PROGRESS_SQL, {"today": date.today().isoformat()}, ttl=30).iloc[0]
    total_di = float(p["total_di"])
    sc = reports.summary_status_counts(_all_spools())
    prog = pd.DataFrame([
        ("Today's date", date.today().strftime("%d-%m-%Y (%A)")),
        ("Today's fit-up (dia-inch)", f"{float(p['today_fitup']):,.2f}"),
        ("Today's welding (dia-inch)", f"{float(p['today_weld']):,.2f}"),
        ("Cumulative fit-up (dia-inch)", f"{float(p['cum_fitup']):,.2f}"),
        ("Cumulative welding (dia-inch)", f"{float(p['cum_weld']):,.2f}"),
        ("Balance fit-up (dia-inch)", f"{total_di - float(p['cum_fitup']):,.2f}"),
        ("Balance welding (dia-inch)", f"{total_di - float(p['cum_weld']):,.2f}"),
        ("Gap fit-up vs inspection (dia-inch)", f"{float(p['cum_fitup']) - float(p['fitup_insp']):,.2f}"),
        ("Gap welding vs inspection (dia-inch)", f"{float(p['cum_weld']) - float(p['weld_insp']):,.2f}"),
        ("Spool: not started", sc["Not Started"]),
        ("Spool: under fabrication", sc["Under Fabrication"]),
        ("Spool: ready to release", sc["Ready to Release"]),
        ("Spool: sent to painting", sc["Sent to Painting"]),
        ("Spool: sent to site", sc["Sent to Site"]),
    ], columns=["Description", "Value"])
    prog["Value"] = prog["Value"].astype(str)
    st.subheader("Progress summary")
    st.dataframe(prog, use_container_width=True, hide_index=True)

    # ---- work order totals ----
    t = db.query(_WO_TOTALS_SQL, ttl=30).iloc[0]
    totals = pd.DataFrame([
        ("Total dia-inch in database", t["total_db"]),
        ("Total dia-inch issued work order", t["issued"]),
        ("Balance dia-inch fit-up (issued W.O.)", t["bal_fitup_issued"]),
        ("Balance dia-inch welding (issued W.O.)", t["bal_weld_issued"]),
        ("Total workable dia-inch", t["workable"]),
        ("Non-workable dia-inch", t["non_workable"]),
        ("Total dia-inch unissued work order", t["unissued"]),
        ("Total dia-inch hold work order", t["hold"]),
        ("Total dia-inch outstanding materials (OS)", t["os"]),
    ], columns=["Description", "Value"])
    totals["Value"] = totals["Value"].astype(float).round(2)
    st.subheader("Work order summary")
    st.dataframe(totals, use_container_width=True, hide_index=True,
                 column_config=num2_cfg(totals))

    st.download_button(
        "⬇ Export to Excel",
        data=reports.build_full_backup_xlsx({
            "Progress Summary": prog,
            "Work Order Issuance": wo_show,
            "Work Order Summary": totals,
        }),
        file_name=f"work_order_summary_{reports.stamp()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def page_update() -> None:
    st.header("Update progress")
    perm = st.session_state.get("permission", "")

    modes = []
    if perm == "all" or "Update Fit-Up" in perm:
        modes.append("Fit-Up date")
    if perm == "all" or "Update Welding" in perm:
        modes.append("Welding date")
    if not modes:
        st.warning("Your account has no update permission "
                   "(needs 'Update Fit-Up' or 'Update Welding').")
        return
    mode = st.radio("What to update", modes, horizontal=True)
    col = "fitup_date" if mode == "Fit-Up date" else "welding_date"

    base = "FROM spools WHERE shop_field='S'"

    iso_opts = db.query(
        f"SELECT DISTINCT iso_dwg_no {base} AND coalesce(iso_dwg_no,'')<>'' ORDER BY 1",
        ttl=0,
    )["iso_dwg_no"].tolist()
    iso = st.selectbox("ISO DWG NO", [""] + iso_opts)
    if not iso:
        return

    line_opts = db.query(
        f"SELECT DISTINCT line_no {base} AND iso_dwg_no=:i AND coalesce(line_no,'')<>'' ORDER BY 1",
        {"i": iso}, ttl=0,
    )["line_no"].tolist()
    line = st.selectbox("LINE NO", [""] + line_opts)
    if not line:
        return

    page_opts = db.query(
        f"SELECT DISTINCT iso_run_no {base} AND iso_dwg_no=:i AND line_no=:l "
        f"AND coalesce(iso_run_no,'')<>'' ORDER BY 1",
        {"i": iso, "l": line}, ttl=0,
    )["iso_run_no"].tolist()
    pageno = st.selectbox("PAGE NO (iso run no)", [""] + page_opts)
    if not pageno:
        return

    spool_opts = db.query(
        f"SELECT DISTINCT dwg_spool_no {base} AND iso_dwg_no=:i AND line_no=:l "
        f"AND iso_run_no=:p AND coalesce(dwg_spool_no,'')<>'' ORDER BY 1",
        {"i": iso, "l": line, "p": pageno}, ttl=0,
    )["dwg_spool_no"].tolist()
    spool = st.selectbox("DWG SPOOL NO", [""] + spool_opts)
    if not spool:
        return

    key = {"i": iso, "l": line, "p": pageno, "s": spool}
    info = db.query(
        f"""SELECT string_agg(DISTINCT nullif(trim(wo_no),''), ', ')      AS wo_no,
                   string_agg(DISTINCT nullif(trim(batch_no),''), ', ')    AS batch_no,
                   string_agg(DISTINCT nullif(trim(area),''), ', ')        AS area,
                   string_agg(DISTINCT nullif(trim(system_no),''), ', ')   AS system_no,
                   string_agg(DISTINCT nullif(trim(test_pack_no),''), ', ') AS test_pack_no,
                   string_agg(DISTINCT nullif(trim(material_group),''), ', ') AS material_group,
                   string_agg(DISTINCT nullif(trim(status),''), ', ')      AS status,
                   count(*) AS joints
            {base} AND iso_dwg_no=:i AND line_no=:l AND iso_run_no=:p AND dwg_spool_no=:s""",
        key, ttl=0,
    ).iloc[0]
    st.markdown(
        f"**WO no:** {info['wo_no'] or '—'} &nbsp;·&nbsp; "
        f"**Batch:** {info['batch_no'] or '—'} &nbsp;·&nbsp; "
        f"**Area:** {info['area'] or '—'} &nbsp;·&nbsp; "
        f"**System:** {info['system_no'] or '—'} &nbsp;·&nbsp; "
        f"**Test pack:** {info['test_pack_no'] or '—'} &nbsp;·&nbsp; "
        f"**Material:** {info['material_group'] or '—'} &nbsp;·&nbsp; "
        f"**Status:** {info['status'] or '—'} &nbsp;·&nbsp; "
        f"**Joints:** {int(info['joints'])}"
    )

    joints = db.query(
        f"""SELECT joint_no, joint_size, item_1, sch_rating_1, item_2, sch_rating_2,
                   coalesce(fitup_date,'')   AS fitup_date,
                   coalesce(welding_date,'') AS welding_date
            {base} AND iso_dwg_no=:i AND line_no=:l AND iso_run_no=:p AND dwg_spool_no=:s
            ORDER BY joint_no""",
        key, ttl=0,
    )
    if joints.empty:
        st.info("No joints for this selection.")
        return
    st.dataframe(joints, use_container_width=True, hide_index=True)

    if col == "fitup_date":
        eligible = joints.loc[joints.fitup_date == "", "joint_no"].tolist()
        locked = joints.loc[joints.fitup_date != "", "joint_no"].tolist()
    else:
        eligible = joints.loc[(joints.fitup_date != "") & (joints.welding_date == ""),
                              "joint_no"].tolist()
        locked = joints.loc[joints.welding_date != "", "joint_no"].tolist()
        no_fitup = joints.loc[joints.fitup_date == "", "joint_no"].tolist()
        if no_fitup:
            st.caption(f"Fit-Up required first: {', '.join(map(str, no_fitup))}")

    if locked:
        st.caption(f"Already set (locked): {', '.join(map(str, locked))}")
    if not eligible:
        st.info("No joints available to update here.")
        return

    picked = st.multiselect("Joint no(s) to update", eligible, default=eligible)
    d = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")
    if st.button(f"Save {mode.lower()}", type="primary"):
        if not picked:
            st.warning("Select at least one joint.")
            return
        db.execute_many(
            f"""UPDATE spools SET {col} = :d
                WHERE iso_dwg_no=:i AND line_no=:l AND iso_run_no=:p
                  AND dwg_spool_no=:s AND joint_no=:j""",
            [{"d": d.isoformat(), "i": iso, "l": line, "p": pageno, "s": spool, "j": j}
             for j in picked],
        )
        try:
            db.execute("INSERT INTO user_log (username) VALUES (:u)",
                       {"u": f"{st.session_state['user']} [{col}]"})
        except Exception:
            pass
        st.success(f"Updated {col} for {len(picked)} joint(s).")
        st.rerun()


# =====================================================================
# QR scan -> update progress   (draft)
#   * a fitter / welder registers his name + PIN once   (Field workers)
#   * the office prints one QR per SPOOL                 (QR labels)
#     - work order / batch / ISO dwg / line / page / dwg spool / material
#   * on the floor he scans the spool, ticks the joints he just did,
#     picks Fit-Up / Welding, keys his PIN, confirms.
#   * a per-joint guarded UPDATE + UNIQUE(qr_id, joint_no, activity) on
#     field_updates make a repeat a no-op ("cannot double entry").
# =====================================================================
@st.cache_resource
def _ensure_qr_schema() -> bool:
    """Idempotent DDL so the QR feature works even if supabase/qr_feature.sql
    wasn't (re-)run. Runs once per server process. Safe to fail silently."""
    stmts = [
        "ALTER TABLE public.spools ADD COLUMN IF NOT EXISTS qr_id text",
        "ALTER TABLE public.spools ADD COLUMN IF NOT EXISTS fitup_by text",
        "ALTER TABLE public.spools ADD COLUMN IF NOT EXISTS welding_by text",
        "ALTER TABLE public.spools ADD COLUMN IF NOT EXISTS welder_no text",
        "DROP INDEX IF EXISTS public.uq_spools_qr_id",          # was UNIQUE in v1
        "CREATE INDEX IF NOT EXISTS idx_spools_qr_id ON public.spools (qr_id)",
        """CREATE TABLE IF NOT EXISTS public.field_workers (
             id bigint generated always as identity primary key,
             name text not null, trade text not null,
             stamp_no text, phone text, pin text not null,
             active boolean not null default true,
             registered_at timestamptz not null default now())""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_field_workers_name_trade "
        "ON public.field_workers (lower(name), trade)",
        """CREATE TABLE IF NOT EXISTS public.field_updates (
             id bigint generated always as identity primary key,
             spool_id bigint not null, qr_id text, joint_no text,
             activity text not null, work_date text not null,
             worker_id bigint, worker_name text, stamp_no text,
             source text not null default 'qr', app_user text,
             recorded_at timestamptz not null default now())""",
        "ALTER TABLE public.field_updates ADD COLUMN IF NOT EXISTS qr_id text",
        "ALTER TABLE public.field_updates ADD COLUMN IF NOT EXISTS joint_no text",
        "DROP INDEX IF EXISTS public.uq_field_updates_joint_activity",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_field_updates_joint_activity "
        "ON public.field_updates (qr_id, joint_no, activity) WHERE qr_id IS NOT NULL",
    ]
    for s in stmts:
        try:
            db.execute(s)
        except Exception:
            pass
    return True


def _field_workers(trade_needed: str) -> pd.DataFrame:
    return db.query(
        """SELECT id, name, trade, coalesce(stamp_no,'') AS stamp_no, pin
             FROM field_workers
            WHERE active AND (trade = :t OR trade = 'Both')
            ORDER BY name""",
        {"t": trade_needed}, ttl=0,
    )


def _register_worker_form(*, key: str, fixed_trade: str | None = None) -> None:
    """Shared 'register a fitter / welder' form (roster page + inline on scan)."""
    with st.form(key, clear_on_submit=True):
        c = st.columns(2)
        name = c[0].text_input("Full name")
        trade = (fixed_trade if fixed_trade
                 else c[1].selectbox("Trade", ["Fitter", "Welder", "Both"]))
        c2 = st.columns(2)
        stamp = c2[0].text_input("Welder No." if fixed_trade == "Fitter"
                                  else "Welder No. (required for welders)")
        phone = c2[1].text_input("Phone (optional)")
        c3 = st.columns(2)
        pin1 = c3[0].text_input("Choose a PIN (4-6 digits)", type="password", max_chars=6)
        pin2 = c3[1].text_input("Confirm PIN", type="password", max_chars=6)
        go = st.form_submit_button("Register", type="primary")
    if not go:
        return
    nm = (name or "").strip()
    sn = (stamp or "").strip()
    p1, p2 = (pin1 or "").strip(), (pin2 or "").strip()
    if not nm:
        st.warning("Enter a name.")
    elif trade in ("Welder", "Both") and not sn:
        st.warning("Welder No. is required for welders.")
    elif not (p1.isdigit() and 4 <= len(p1) <= 6):
        st.warning("PIN must be 4 to 6 digits.")
    elif p1 != p2:
        st.warning("The two PINs don't match.")
    else:
        try:
            db.execute(
                """INSERT INTO field_workers (name, trade, stamp_no, phone, pin)
                   VALUES (:n, :t, :s, :ph, :pin)""",
                {"n": nm, "t": trade, "s": sn,
                 "ph": phone.strip() or None, "pin": p1},
            )
            st.cache_data.clear()
            st.success(f"Registered {nm} ({trade}).")
            st.rerun()
        except Exception as e:
            if "uq_field_workers" in str(e) or "duplicate" in str(e).lower():
                st.error(f"{nm} is already registered as {trade}.")
            else:
                st.error(f"Could not register: {e}")


def _scan_history(code: str) -> None:
    h = db.query(
        """SELECT activity,
                  coalesce(joint_no,'')    AS joint,
                  work_date,
                  coalesce(worker_name,'') AS worker,
                  coalesce(stamp_no,'')    AS "Welder No.",
                  to_char(recorded_at AT TIME ZONE 'Asia/Kuala_Lumpur',
                          'YYYY-MM-DD HH24:MI') AS recorded
             FROM field_updates WHERE qr_id = :c
            ORDER BY recorded_at""",
        {"c": code}, ttl=0,
    )
    if not h.empty:
        st.caption("Scan history for this spool")
        st.dataframe(h, use_container_width=True, hide_index=True)


def page_scan() -> None:
    st.header("📲 Scan & update")
    _ensure_qr_schema()

    code = (st.query_params.get("scan")
            or st.session_state.get("pending_scan") or "").strip()
    code = st.text_input("Spool QR code", value=code,
                         help="Scanned from the phone camera, or type the code "
                              "printed under the QR.").strip().upper()
    if not code:
        st.info("Scan a spool's QR label with your phone camera, or key its code above.")
        return

    try:
        js = db.query(
            """SELECT id, joint_no, joint_size,
                      coalesce(wo_no,'')          AS wo_no,
                      coalesce(batch_no,'')       AS batch_no,
                      coalesce(iso_dwg_no,'')     AS iso_dwg_no,
                      coalesce(line_no,'')        AS line_no,
                      coalesce(iso_run_no,'')     AS iso_run_no,
                      coalesce(dwg_spool_no,'')   AS dwg_spool_no,
                      coalesce(area,'')           AS area,
                      coalesce(service,'')        AS service,
                      coalesce(material_group,'') AS material_group,
                      coalesce(paint_system,'')   AS paint_system,
                      coalesce(fitup_date,'')     AS fitup_date,
                      coalesce(welding_date,'')   AS welding_date,
                      coalesce(fitup_by,'')       AS fitup_by,
                      coalesce(welding_by,'')     AS welding_by
                 FROM spools WHERE qr_id = :c
                ORDER BY joint_no""",
            {"c": code}, ttl=0,
        )
    except Exception as e:
        if "qr_id" in str(e).lower():
            st.error("This database isn't set up for QR yet. Run "
                     "**supabase/qr_feature.sql** in Supabase, then assign codes "
                     "on the **QR labels** page.")
        else:
            st.error(f"Lookup failed: {e}")
        return

    if js.empty:
        try:
            total = int(db.query("SELECT count(*) n FROM spools "
                                 "WHERE coalesce(qr_id,'')<>''", ttl=0).iloc[0]["n"])
        except Exception:
            total = 0
        if total == 0:
            st.warning("No QR codes have been assigned yet. On the **QR labels** "
                       "page (admin) click **Assign / top-up codes**, then build "
                       "and print a fresh sheet.")
        else:
            st.error(f"Code **{code}** isn't in the database ({total:,} spools do "
                     "have codes). Make sure the label came from **this** site's "
                     "QR labels page — not an older or sample sheet — or re-assign "
                     "and reprint.")
        return

    uniq = lambda col: ", ".join(sorted({x for x in js[col] if x})) or "—"
    _psize = ", ".join(sorted(
        {f"{float(x):g}" for x in js["joint_size"] if pd.notna(x)},
        key=lambda s: float(s))) or "—"
    _info = [
        ("ISO", uniq("iso_dwg_no")),
        ("SPOOL NO.", uniq("dwg_spool_no")),
        ("AREA", uniq("area")),
        ("SERVICE", uniq("service")),
        ("PIPE SIZE", _psize),
        ("RUN / ISO NO", uniq("iso_run_no")),
        ("PAINT CODE", uniq("paint_system")),
        ("WO", uniq("wo_no")),
        ("LINE", uniq("line_no")),
        ("BATCH", uniq("batch_no")),
        ("MATERIAL", uniq("material_group")),
    ]
    _rows = "".join(
        "<tr>"
        "<td style='padding:4px 16px 4px 0;color:var(--muted);font-size:.82rem;"
        "font-weight:700;letter-spacing:.06em;white-space:nowrap;"
        "vertical-align:baseline'>" + lbl + "</td>"
        "<td style='padding:4px 0;color:var(--ink);font-size:1.2rem;"
        "font-weight:700;line-height:1.35'>" + html.escape(str(val)) + "</td>"
        "</tr>"
        for lbl, val in _info
    )
    st.markdown(
        "<table style='border-collapse:collapse;margin:.1rem 0 .6rem'>"
        + _rows + "</table>",
        unsafe_allow_html=True,
    )

    n = len(js)
    m1, m2 = st.columns(2)
    m1.metric("Fit-Up", f"{int((js['fitup_date'] != '').sum())}/{n}")
    m2.metric("Welding", f"{int((js['welding_date'] != '').sum())}/{n}")

    view = js[["joint_no", "joint_size", "fitup_date", "fitup_by",
               "welding_date", "welding_by"]].copy()
    view["joint_size"] = pd.to_numeric(view["joint_size"], errors="coerce")
    view.columns = ["Joint", "Size", "Fit-Up", "Fitter", "Welding", "Welder"]
    st.dataframe(view, use_container_width=True, hide_index=True)

    # Who is updating — the activity follows their trade:
    #   Fitter -> Fit-Up only,  Welder -> Welding only,  Both -> choose.
    allw = db.query(
        "SELECT id, name, trade, coalesce(stamp_no,'') AS stamp_no, pin "
        "FROM field_workers WHERE active ORDER BY name", ttl=0,
    )
    with st.expander("➕ New fitter / welder? Register your name"):
        _register_worker_form(key="reg_scan")
    if allw.empty:
        st.warning("No fitter / welder registered yet — register above, then it "
                   "appears here.")
        return

    # Tap-to-fill recent names - this is server-side (who last used the app,
    # not this device), so unlike a browser-remembered value it still works
    # even though a fresh QR scan opens a brand-new, blank browser tab/session
    # every time (that's why the text box itself can't "stay" pre-filled).
    recent = db.query(
        """SELECT worker_name, max(recorded_at) AS last_at
             FROM field_updates WHERE coalesce(worker_name,'') <> ''
            GROUP BY worker_name ORDER BY last_at DESC LIMIT 5""",
        ttl=15,
    )["worker_name"].tolist()
    if recent:
        st.caption("Recent")
        rc = st.columns(len(recent))
        for i, nm in enumerate(recent):
            if rc[i].button(nm, key=f"recent_{i}", use_container_width=True):
                st.session_state["scan_who_text"] = nm
                st.rerun()

    # A plain text box (not a combo/selectbox) so the phone keyboard always
    # opens; matched against the roster as you type. key= (not value=) is
    # what makes Streamlit remember what was typed across reruns in this
    # same browser tab.
    _names = allw["name"].tolist()
    q = st.text_input("Your name", key="scan_who_text",
                      placeholder="Type your name, or tap a recent name above…").strip()
    who = None
    if q:
        exact = [n for n in _names if n.lower() == q.lower()]
        matches = exact or [n for n in _names if q.lower() in n.lower()]
        if len(matches) == 1:
            who = matches[0]
            st.caption(f"✓ {who}")
        elif matches:
            who = st.radio("Which one is you?", matches, key="scan_who_pick")
        else:
            st.warning(f"No fitter/welder matches \"{q}\". Check spelling, or "
                       "register above.")
    if not who:
        st.info("Type your name above to continue.")
        _scan_history(code)
        return
    wrow = allw.loc[allw["name"] == who].iloc[0]
    wtrade = str(wrow["trade"])

    if wtrade == "Fitter":
        activity = "Fit-Up"
    elif wtrade == "Welder":
        activity = "Welding"
    else:                                        # Both
        activity = st.radio("Activity just completed", ["Fit-Up", "Welding"],
                            horizontal=True)
    st.caption(f"**{who}** · {wtrade} → recording **{activity}**")

    col = "fitup_date" if activity == "Fit-Up" else "welding_date"
    if activity == "Fit-Up":
        elig = js.loc[js["fitup_date"] == "", "joint_no"].tolist()
        none_msg = "Every joint on this spool is already fitted-up."
    else:
        elig = js.loc[(js["fitup_date"] != "") & (js["welding_date"] == ""),
                      "joint_no"].tolist()
        pend = js.loc[js["fitup_date"] == "", "joint_no"].tolist()
        if pend:
            st.caption("Fit-Up needed first: " + ", ".join(map(str, pend)))
        none_msg = "No joints on this spool are waiting for welding."

    if not elig:
        st.info(none_msg)
        _scan_history(code)
        return

    picked = st.multiselect(f"Joints to mark {activity} complete", elig, default=elig)
    pin = st.text_input("Your PIN", type="password", max_chars=6)
    wd = st.date_input("Date completed", value=date.today(), format="DD/MM/YYYY")

    if st.button(f"✅ Confirm {activity} for {len(picked)} joint(s)", type="primary",
                 use_container_width=True, disabled=not picked):
        if (pin or "").strip() != str(wrow["pin"]):
            st.error("Wrong PIN.")
            return

        seq = " AND coalesce(fitup_date,'') <> '' " if activity == "Welding" else ""
        by_col = "fitup_by" if activity == "Fit-Up" else "welding_by"
        # also stamp the welder's Welder No. onto the spool, beside
        # capping_welder_no, when it's a welding update
        extra_set = ", welder_no = :sn" if activity == "Welding" else ""
        one = (
            f"WITH upd AS ( UPDATE spools SET {col} = :d, {by_col} = :wn{extra_set} "
            f"WHERE qr_id = :c AND joint_no = :j AND coalesce({col},'') = '' {seq} "
            "RETURNING id ) "
            "INSERT INTO field_updates (spool_id, qr_id, joint_no, activity, "
            "work_date, worker_id, worker_name, stamp_no, source, app_user) "
            "SELECT id, :c, :j, :a, :d, :wid, :wn, :sn, 'qr', :au FROM upd"
        )
        b = {"d": wd.isoformat(), "c": code, "a": activity, "wid": int(wrow["id"]),
             "wn": who, "sn": (wrow["stamp_no"] or None),
             "au": st.session_state.get("user")}
        saved, skipped = [], []
        for j in picked:
            try:
                got = db.write(one, {**b, "j": j})
            except Exception as e:
                msg = str(e).lower()
                if "uq_field_updates" in msg or "duplicate key" in msg:
                    got = 0
                else:
                    st.error(f"Joint {j}: {e}")
                    continue
            (saved if got else skipped).append(str(j))
        if saved:
            st.success(f"{activity} recorded for joint(s) {', '.join(saved)} "
                       f"by {who} on {wd:%d/%m/%Y}. Terima kasih!")
        if skipped:
            st.warning("Already recorded, left as-is (no double entry): "
                       + ", ".join(skipped))
        st.cache_data.clear()
        st.rerun()

    _scan_history(code)


def page_field_workers() -> None:
    st.header("🦺 Field workers")
    _ensure_qr_schema()
    st.caption("The shop-floor roster. Fitters and welders can also self-register "
               "from the Scan & update screen; the name + PIN signs every scan.")
    is_admin = st.session_state.get("permission", "") == "all"

    st.subheader("Register")
    _register_worker_form(key="reg_fw")

    st.divider()
    st.subheader("Registered")
    df = db.query(
        """SELECT id, name, trade,
                  coalesce(stamp_no,'') AS "Welder No.",
                  coalesce(phone,'')    AS phone, pin, active,
                  to_char(registered_at AT TIME ZONE 'Asia/Kuala_Lumpur',
                          'YYYY-MM-DD') AS since
             FROM field_workers ORDER BY active DESC, name""",
        ttl=0,
    )
    if df.empty:
        st.info("Nobody registered yet.")
        return
    show_pin = is_admin and st.checkbox("Show PINs", value=False)
    disp = df.drop(columns=["id"])
    if not show_pin:
        disp = disp.assign(pin="••••")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    if is_admin:
        st.markdown("**Admin**")
        labels = (df["name"] + "  ·  " + df["trade"]).tolist()
        cc = st.columns([3, 1, 1])
        pick = cc[0].selectbox("Worker", labels, label_visibility="collapsed")
        sel = df.iloc[labels.index(pick)]
        if cc[1].button("Toggle active", use_container_width=True):
            db.execute("UPDATE field_workers SET active = NOT active WHERE id = :i",
                       {"i": int(sel["id"])})
            st.cache_data.clear()
            st.rerun()
        if cc[2].button("🗑 Delete", use_container_width=True):
            try:
                db.execute("DELETE FROM field_workers WHERE id = :i",
                           {"i": int(sel["id"])})
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Can't delete — this worker already has scan history. "
                         "Toggle them inactive instead.")


# the fields that make one spool = one QR
# A spool = these four fields (same definition the dashboard uses). WO /
# batch / material are shown on the label but NOT part of the key - they
# can differ joint-to-joint and would otherwise split one spool into many.
_SPOOL_KEY = ("iso_dwg_no", "line_no", "iso_run_no", "dwg_spool_no")


def page_qr_labels() -> None:
    st.header("🏷️ QR labels")
    _ensure_qr_schema()
    st.caption("One QR per spool (ISO dwg · line · page · dwg spool). The label "
               "also prints WO / batch / material. Scanning it lists every joint "
               "on that spool to update.")

    settings = db.get_settings()
    saved_url = settings.get("app_url", "")
    typed = st.text_input(
        "App URL (goes inside every QR)", value=saved_url,
        placeholder="https://your-app.streamlit.app",
        help="Just the site address — no ?theme=… or other bits. Anything after "
             "the domain is stripped automatically.",
    )
    base = qr.clean_base(typed)               # drop any pasted ?query / #fragment
    if base and base != typed.strip():
        st.caption(f"Will use: `{base}`")
    if base and base != saved_url and st.button("Save app URL"):
        db.set_settings({"app_url": base})
        st.success(f"Saved `{base}`.")
        st.rerun()
    elif saved_url and qr.clean_base(saved_url) != saved_url:
        st.warning(f"The saved URL has extra bits — click **Save app URL** to "
                   f"fix it to `{qr.clean_base(saved_url)}`, then rebuild the sheet.")

    # -- kiosk sign-in: bake &k=<token> into every QR so the phone never
    #    sees the login screen (auto-signs-in as a scan-only account) ------
    with st.expander("📵 Skip the login screen on the shop floor (kiosk mode)",
                     expanded=bool(settings.get("kiosk_token"))):
        st.caption("Bakes a token into every QR that auto-signs-in as the "
                   "account below — no username / password on the phone. Use it "
                   "**only** with an account that has just the shop-floor QR "
                   "grant: anyone who photographs a label can open the scan tab "
                   "as that account (each scan is still signed with the "
                   "worker's own name + PIN). Re-print the labels after you "
                   "enable or regenerate.")
        _users = db.query("SELECT username, permission FROM user_credentials "
                          "ORDER BY username", ttl=0)
        _scan_only = [u for u, p in zip(_users["username"], _users["permission"])
                      if {t.strip() for t in str(p).split(",")} == {"Field Scan"}]
        _opts = _scan_only or list(_users["username"])
        cur_user = settings.get("kiosk_user", "")
        idx = _opts.index(cur_user) if cur_user in _opts else 0
        ku = st.selectbox("Auto-sign-in as", _opts, index=idx,
                          help="Recommended: an account with only 'Shop-floor QR scan'.")
        cc = st.columns(2)
        if cc[0].button("Enable / regenerate token", type="primary"):
            db.set_settings({"kiosk_token": qr.new_code(16), "kiosk_user": ku})
            st.cache_data.clear()
            st.success("Kiosk enabled. Re-build and re-print the label sheet.")
            st.rerun()
        if settings.get("kiosk_token"):
            if cc[1].button("Disable kiosk"):
                db.set_settings({"kiosk_token": "", "kiosk_user": ""})
                st.cache_data.clear()
                st.success("Kiosk disabled. Labels now open the login screen.")
                st.rerun()
            st.info(f"Active — QRs auto-sign-in as **{settings.get('kiosk_user','?')}**.")

    kiosk_token = settings.get("kiosk_token", "")

    gcond = " AND ".join(f"coalesce(s.{c},'') = coalesce(g.{c},'')" for c in _SPOOL_KEY)
    grp = ", ".join(_SPOOL_KEY)

    stat = db.query(
        f"""WITH g AS (
              SELECT {grp}, bool_or(coalesce(qr_id,'')<>'') AS coded
                FROM spools WHERE shop_field='S' GROUP BY {grp}
            )
            SELECT count(*) FILTER (WHERE coded)          AS have,
                   count(*) FILTER (WHERE NOT coded)      AS miss,
                   count(*)                                AS total
              FROM g""",
        ttl=0,
    ).iloc[0]
    have, miss = int(stat["have"]), int(stat["miss"])
    # joints that belong to a coded spool but have no code yet (added by re-import)
    partial = int(db.query(
        f"""SELECT count(*) n FROM spools s
             WHERE s.shop_field='S' AND coalesce(s.qr_id,'')=''
               AND EXISTS (SELECT 1 FROM spools g
                           WHERE g.shop_field='S' AND coalesce(g.qr_id,'')<>''
                             AND {gcond})""",
        ttl=0,
    ).iloc[0]["n"])

    st.write(f"Spools with a code: **{have}**  ·  without: **{miss}**"
             + (f"  ·  loose joints to top up: **{partial}**" if partial else ""))

    if (miss or partial) and st.button(
            f"Assign / top-up codes ({miss} new, {partial} joints)", type="primary"):
        filled = 0
        if partial:
            filled = db.write(
                f"""UPDATE spools s SET qr_id = x.code
                      FROM (SELECT {grp}, max(qr_id) AS code FROM spools
                             WHERE shop_field='S' AND coalesce(qr_id,'')<>''
                             GROUP BY {grp}) x
                     WHERE s.shop_field='S' AND coalesce(s.qr_id,'')=''
                       AND {" AND ".join(f"coalesce(s.{c},'')=coalesce(x.{c},'')" for c in _SPOOL_KEY)}"""
            )
        groups = db.query(
            f"""SELECT {", ".join(f"coalesce({c},'') AS {c}" for c in _SPOOL_KEY)}
                  FROM spools WHERE shop_field='S'
                 GROUP BY {grp} HAVING bool_and(coalesce(qr_id,'')='')""",
            ttl=0,
        )
        if not groups.empty:
            cond = " AND ".join(f"coalesce({c},'') = :{c}" for c in _SPOOL_KEY)
            try:
                db.execute_many(
                    f"UPDATE spools SET qr_id = :qc "
                    f"WHERE shop_field='S' AND coalesce(qr_id,'')='' AND {cond}",
                    [{**{c: row[c] for c in _SPOOL_KEY}, "qc": qr.new_code()}
                     for _, row in groups.iterrows()],
                )
            except Exception as e:
                if "unique" in str(e).lower() or "uq_spools_qr_id" in str(e):
                    st.error("An old unique index on qr_id is still on the "
                             "database. Re-run **supabase/qr_feature.sql** in "
                             "Supabase, then try again.")
                    return
                raise
        st.cache_data.clear()
        st.success(f"Coded {len(groups)} new spool(s)"
                   + (f", topped up {filled} joint(s)." if filled else "."))
        st.rerun()

    with st.expander("Re-code every spool (wipe and start over)"):
        st.caption("Use this if the codes were built with a different spool "
                   "grouping (e.g. one QR per joint). It clears every shop qr_id "
                   "and assigns one fresh code per spool. Scan history stays "
                   "readable but stops linking to the joint. Re-print afterwards.")
        if st.button("♻ Wipe & re-code all shop spools"):
            try:
                db.execute("DROP INDEX IF EXISTS public.uq_spools_qr_id")
            except Exception:
                pass
            db.write("UPDATE spools SET qr_id = NULL WHERE shop_field='S'")
            fresh = db.query(
                f"""SELECT {", ".join(f"coalesce({c},'') AS {c}" for c in _SPOOL_KEY)}
                      FROM spools WHERE shop_field='S' GROUP BY {grp}""",
                ttl=0,
            )
            cond = " AND ".join(f"coalesce({c},'') = :{c}" for c in _SPOOL_KEY)
            db.execute_many(
                f"UPDATE spools SET qr_id = :qc "
                f"WHERE shop_field='S' AND coalesce(qr_id,'')='' AND {cond}",
                [{**{c: row[c] for c in _SPOOL_KEY}, "qc": qr.new_code()}
                 for _, row in fresh.iterrows()],
            )
            st.cache_data.clear()
            st.success(f"Re-coded {len(fresh)} spool(s). Rebuild and re-print.")
            st.rerun()

    st.divider()
    st.subheader("Print sheet")
    scope = st.radio("Which spools",
                     ["By work order", "By batch", "By ISO drawing", "All shop spools"],
                     horizontal=True)
    filt, params = "", {}
    _pick_from = lambda c: db.query(
        f"SELECT DISTINCT {c} v FROM spools WHERE shop_field='S' "
        f"AND coalesce({c},'')<>'' ORDER BY 1", ttl=0)["v"].tolist()
    if scope == "By work order":
        params = {"v": st.selectbox("WO no", _pick_from("wo_no"))}
        filt = "AND wo_no = :v"
    elif scope == "By batch":
        params = {"v": st.selectbox("Batch no", _pick_from("batch_no"))}
        filt = "AND batch_no = :v"
    elif scope == "By ISO drawing":
        params = {"v": st.selectbox("ISO DWG NO", _pick_from("iso_dwg_no"))}
        filt = "AND iso_dwg_no = :v"

    rows = db.query(
        f"""SELECT qr_id,
                   string_agg(DISTINCT nullif(wo_no,''), ', ')          AS wo,
                   string_agg(DISTINCT nullif(batch_no,''), ', ')       AS batch,
                   string_agg(DISTINCT nullif(iso_dwg_no,''), ', ')     AS iso,
                   string_agg(DISTINCT nullif(line_no,''), ', ')        AS line,
                   string_agg(DISTINCT nullif(iso_run_no,''), ', ')     AS page,
                   string_agg(DISTINCT nullif(dwg_spool_no,''), ', ')   AS spool,
                   string_agg(DISTINCT nullif(area,''), ', ')           AS area,
                   string_agg(DISTINCT nullif(service,''), ', ')        AS service,
                   string_agg(DISTINCT nullif(material_group,''), ', ') AS material,
                   string_agg(DISTINCT nullif(paint_system,''), ', ')   AS paint,
                   to_char(max(joint_size), 'FM999990.###')             AS size,
                   count(*)                                              AS joints
              FROM spools
             WHERE shop_field='S' AND coalesce(qr_id,'')<>'' {filt}
             GROUP BY qr_id
             ORDER BY 4, 7""",
        params, ttl=0,
    )
    st.write(f"{len(rows)} label(s) ready — PDF is one sticker per page "
             f"({qr.LABEL_W_CM} × {qr.LABEL_H_CM} cm). Print at 100% / actual size.")

    if not rows.empty and st.button("Build label PDF", type="primary"):
        if not base:
            st.warning("Set the App URL first — without it the QR codes open nothing.")
        else:
            try:
                pdf = qr.labels_pdf(rows.to_dict("records"), base,
                                    kiosk_token=kiosk_token)
                st.download_button("⬇ Download labels (PDF)", pdf,
                                   file_name=f"qr_labels_{reports.stamp()}.pdf",
                                   mime="application/pdf", type="primary")
            except ModuleNotFoundError:
                st.error("The server doesn't have the 'qrcode' package yet. Add "
                         "`qrcode[pil]` to requirements.txt and redeploy.")


def page_delivery() -> None:
    st.header("Delivery")
    perm = st.session_state.get("permission", "")

    modes = []
    if perm == "all" or "Painting Delivery" in perm:
        modes.append("Painting delivery")
    if perm == "all" or "Site Delivery" in perm:
        modes.append("Site delivery")
    if not modes:
        st.warning("Needs 'Painting Delivery' or 'Site Delivery' permission.")
        return
    mode = st.radio("What to update", modes, horizontal=True)
    _delivery_worklist("painting" if mode == "Painting delivery" else "site")


def _delivery_worklist(kind: str) -> None:
    painting = kind == "painting"
    do_col, dt_col = (("delivery_order_no", "delivery_date") if painting
                      else ("site_do_no", "site_delivery_date"))
    do_label = "Painting DO no" if painting else "Site DO no"
    verb = "painting delivery" if painting else "site delivery"

    if painting:
        pending = ("coalesce(trim(paint_system),'')<>'' "
                   "AND coalesce(trim(delivery_date),'')=''")
        st.caption("Spools that **need painting** (paint system filled) and haven't "
                   "been sent yet. Blank paint system = no painting, not shown here.")
    else:
        pending = ("coalesce(trim(site_delivery_date),'')='' "
                   "AND (coalesce(trim(delivery_date),'')<>'' "
                   "OR coalesce(trim(paint_system),'')='')")
        st.caption("Spools ready for **site**: already sent to painting **or** no "
                   "painting needed (blank paint system), and not yet sent to site.")

    only_welded = st.toggle("Only welding-complete spools", value=True)
    having = "HAVING bool_and(coalesce(trim(welding_date),'')<>'')" if only_welded else ""
    df = db.query(
        f"""
        SELECT iso_dwg_no, line_no, iso_run_no AS page_no, dwg_spool_no,
               coalesce(max(paint_system),'')                     AS paint_system,
               max(delivery_date)                                 AS painting_date,
               count(*)                                           AS joints,
               round(sum(joint_size)::numeric, 2)                 AS dia_inch,
               bool_and(coalesce(trim(welding_date),'')<>'')      AS welded
        FROM spools
        WHERE shop_field='S' AND {pending}
        GROUP BY 1,2,3,4
        {having}
        ORDER BY 1,2,3,4
        """,
        ttl=0,
    )
    if df.empty:
        st.success(f"Nothing pending {verb}.")
    else:
        df["dia_inch"] = df["dia_inch"].astype(float)
        df["joints"] = df["joints"].astype(int)
        df.insert(0, "Send", False)

        edited = st.data_editor(
            df, hide_index=True, use_container_width=True, key=f"{kind}_worklist",
            column_config={"Send": st.column_config.CheckboxColumn("Send", default=False)},
            disabled=[c for c in df.columns if c != "Send"],
        )
        picked = edited[edited["Send"]]
        st.write(f"**{len(picked)}** spool(s) selected · "
                 f"**{picked['dia_inch'].sum():,.2f}** dia-inch · "
                 f"**{int(picked['joints'].sum())}** joint(s)")

        c = st.columns(2)
        do_no = c[0].text_input(do_label)
        d = c[1].date_input("Delivery date", value=date.today(), format="YYYY-MM-DD")
        confirm = st.checkbox(f"Confirm — record {verb} for the ticked spools")
        if st.button(f"Record {verb}", type="primary", disabled=not confirm):
            if picked.empty or not do_no.strip():
                st.warning("Tick at least one spool and enter a DO no.")
                return
            db.execute_many(
                f"""UPDATE spools SET {do_col}=:do, {dt_col}=:d
                    WHERE shop_field='S' AND iso_dwg_no=:i AND line_no=:l
                      AND iso_run_no=:p AND dwg_spool_no=:s""",
                [{"do": do_no.strip(), "d": d.isoformat(), "i": r.iso_dwg_no,
                  "l": r.line_no, "p": r.page_no, "s": r.dwg_spool_no}
                 for r in picked.itertuples()],
            )
            try:
                db.execute("INSERT INTO user_log (username) VALUES (:u)",
                           {"u": f"{st.session_state['user']} [{kind} DO {do_no.strip()} "
                                 f"x{len(picked)}]"})
            except Exception:
                pass
            st.cache_data.clear()
            st.success(f"Recorded {verb} DO {do_no.strip()} for {len(picked)} spool(s).")
            st.rerun()

    with st.expander(f"Already sent ({'painting' if painting else 'site'})"):
        st.dataframe(
            db.query(
                f"""SELECT iso_dwg_no, line_no, iso_run_no AS page_no, dwg_spool_no,
                           max({do_col}) AS do_no, max({dt_col}) AS date,
                           count(*) AS joints
                    FROM spools
                    WHERE shop_field='S' AND coalesce(trim({dt_col}),'')<>''
                    GROUP BY 1,2,3,4 ORDER BY 6 DESC, 1""",
                ttl=0,
            ),
            use_container_width=True, hide_index=True,
        )


@st.cache_data(ttl=120)
def _distinct(col: str) -> list:
    return [x for x in db.query(
        f"SELECT DISTINCT {col} FROM spools WHERE coalesce(trim({col}::text),'')<>'' "
        f"ORDER BY 1", ttl=120)[col].tolist()]


def page_spools() -> None:
    st.header("Spools")
    q = st.text_input("🔎 Search (WO / ISO / spool / joint / test pack / line)",
                      placeholder="type any part…")
    fcol = st.columns(4)
    area = fcol[0].multiselect("Area", _distinct("area"))
    batch = fcol[1].multiselect("Batch no", _distinct("batch_no"))
    shop = fcol[2].selectbox("Shop/Field", ["", "S", "F"])
    status = fcol[3].selectbox("Status", ["", "issued", "os", "hold"])
    g1, g2 = st.columns(2)
    only_fit = g1.checkbox("Fitted only")
    only_weld = g2.checkbox("Welded only")

    where, params = [], {}
    if q.strip():
        where.append("(wo_no ILIKE :q OR iso_dwg_no ILIKE :q OR dwg_spool_no ILIKE :q "
                     "OR joint_no ILIKE :q OR test_pack_no ILIKE :q OR line_no ILIKE :q)")
        params["q"] = f"%{q.strip()}%"
    if area:
        where.append("area = ANY(:area)"); params["area"] = area
    if batch:
        where.append("batch_no = ANY(:batch)"); params["batch"] = batch
    if shop:
        where.append("shop_field = :shop"); params["shop"] = shop
    if status:
        where.append("status = :status"); params["status"] = status
    if only_fit:
        where.append("coalesce(trim(fitup_date),'')<>''")
    if only_weld:
        where.append("coalesce(trim(welding_date),'')<>''")
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    n = db.query(f"SELECT count(*) c FROM spools {clause}", params).iloc[0]["c"]
    st.caption(f"{n:,} rows match — showing up to 2000")
    df = db.query(
        f"""
        SELECT id, wo_no, batch_no, iso_dwg_no, dwg_spool_no, joint_no, joint_size,
               area, system_no, test_pack_no, shop_field, status,
               fitup_date, welding_date, paint_status, painting_date, delivery_date,
               site_delivery_date, workable
        FROM spools {clause}
        ORDER BY iso_dwg_no, dwg_spool_no, joint_no
        LIMIT 2000
        """,
        params,
    )
    show_table(df, "spools", money=("joint_size",))


@st.cache_data(ttl=30)
def _all_spools() -> pd.DataFrame:
    return db.query("SELECT * FROM spools", ttl=30)


@st.cache_data(ttl=600, show_spinner="Classifying spools & building exports…")
def _classify_payload():
    """Heavy work (classify + two formatted xlsx workbooks) done once, cached.
    Cleared by st.cache_data.clear() after any spools import/restore."""
    df = db.query("SELECT * FROM spools", ttl=600)
    classified = reports.classify(df)
    preview = classified[[c for c in reports._CLASSIFIED_COLS if c in classified.columns]]
    return (
        reports.summarize(classified),
        preview,
        reports.build_classified_xlsx(df),
        reports.build_master_xlsx(df),
        int(len(df)),
    )


def page_reports() -> None:
    st.header("Classify & export")
    summary, preview, x_classified, x_master, nrows = _classify_payload()

    top = st.columns([4, 1])
    top[0].caption(f"{nrows:,} spools · ported from classify_spools.py / export_master.py "
                   "· results cached ~10 min")
    if top[1].button("↻ Rebuild", use_container_width=True):
        _classify_payload.clear()
        st.rerun()

    st.subheader("Spool status summary")
    st.dataframe(
        summary, use_container_width=True, hide_index=True,
        column_config={
            "Dia-Inch": st.column_config.NumberColumn(format="%.2f"),
            "% Spools": st.column_config.NumberColumn(format="%.1f%%"),
            "% Dia-Inch": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    st.bar_chart(summary.set_index("Spool Status")["Pipe Spools"])

    ts = reports.stamp()
    _XL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇  Download classified spools (.xlsx)", data=x_classified,
            file_name=f"classified_spools_{ts}.xlsx", mime=_XL,
            type="primary", use_container_width=True,
        )
        st.caption("Summary + All Spools + Pipe Spool Summary + one sheet per status.")
    with c2:
        st.download_button(
            "⬇  Download master export (.xlsx)", data=x_master,
            file_name=f"spool_tracking_{ts}.xlsx", mime=_XL,
            type="primary", use_container_width=True,
        )
        st.caption("Full spools table with report headers, desktop column order.")

    with st.expander("Preview: classified rows"):
        st.dataframe(preview, use_container_width=True, hide_index=True)


_WCS_DDL = """
CREATE TABLE IF NOT EXISTS qc_wcs_docs (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    filename    text NOT NULL, mime text, size_bytes bigint, data bytea NOT NULL,
    note text, uploaded_by text,
    uploaded_at timestamptz NOT NULL DEFAULT now()
)
"""
_WCS_MAX_MB = 25


@st.cache_data(ttl=600, show_spinner="Fetching document…")
def _wcs_bytes(doc_id: int) -> bytes:
    # raw engine, not db.query() — Streamlit's SQL-connection cache can't
    # serialize a DataFrame that holds a bytea column.
    from sqlalchemy import text as _t
    with db.engine().connect() as cx:
        row = cx.execute(_t("SELECT data FROM qc_wcs_docs WHERE id = :i"),
                         {"i": doc_id}).first()
    return bytes(row[0]) if row and row[0] is not None else b""


def page_qc_wcs() -> None:
    st.header("QC WCS documents")
    perm = st.session_state.get("permission", "")
    can_upload = perm == "all" or "QC WCS" in perm

    from sqlalchemy import text as _t
    with db.engine().begin() as cx:
        cx.execute(_t(_WCS_DDL))

    if can_upload:
        with st.form("wcs_upload", clear_on_submit=True):
            files = st.file_uploader(
                "Add document(s)", accept_multiple_files=True,
                type=["pdf", "xlsx", "xls", "docx", "doc", "jpg", "jpeg", "png",
                      "zip", "csv", "txt"],
            )
            note = st.text_input("Note / reference (optional)")
            go = st.form_submit_button("⬆  Upload", type="primary",
                                       use_container_width=True)
        if go:
            if not files:
                st.warning("Choose at least one file.")
            else:
                ok = 0
                for f in files:
                    b = f.getvalue()
                    if len(b) > _WCS_MAX_MB * 1024 * 1024:
                        st.error(f"{f.name}: {len(b)/1e6:.1f} MB exceeds the "
                                 f"{_WCS_MAX_MB} MB limit — skipped.")
                        continue
                    db.execute(
                        """INSERT INTO qc_wcs_docs
                             (filename, mime, size_bytes, data, note, uploaded_by)
                           VALUES (:fn, :mt, :sz, :dt, :nt, :ub)""",
                        {"fn": f.name, "mt": f.type, "sz": len(b), "dt": b,
                         "nt": note.strip() or None, "ub": st.session_state["user"]},
                    )
                    ok += 1
                if ok:
                    st.cache_data.clear()
                    st.success(f"Uploaded {ok} file(s) — time-stamped "
                               f"{pd.Timestamp.now(tz='Asia/Kuala_Lumpur'):%Y-%m-%d %H:%M} MYT.")
                    st.rerun()
    else:
        st.caption("Download only — needs the **QC WCS uploads** grant to add documents.")

    meta = db.query(
        """SELECT id, filename, coalesce(note,'') AS note,
                  coalesce(uploaded_by,'') AS uploaded_by,
                  to_char(uploaded_at AT TIME ZONE 'Asia/Kuala_Lumpur',
                          'YYYY-MM-DD HH24:MI') AS uploaded_at,
                  size_bytes
           FROM qc_wcs_docs ORDER BY uploaded_at DESC, id DESC""",
        ttl=0,
    )
    st.subheader(f"Documents ({len(meta)})")
    if meta.empty:
        st.info("No documents uploaded yet.")
        return

    q = st.text_input("Filter by file name")
    view = meta[meta["filename"].str.contains(q.strip(), case=False, na=False)] if q.strip() else meta

    disp = view.assign(size=(view["size_bytes"] / 1024).round(0).astype("Int64").astype(str) + " KB")
    st.dataframe(
        disp[["filename", "note", "uploaded_by", "uploaded_at", "size"]],
        use_container_width=True, hide_index=True,
        column_config={"uploaded_at": st.column_config.TextColumn("uploaded (date & time)")},
    )

    st.subheader("Download")
    if view.empty:
        st.caption("No match.")
        return
    sel = st.selectbox(
        "Document", view["id"].tolist(),
        format_func=lambda i: view.loc[view["id"] == i, "filename"].iloc[0],
    )
    row = view[view["id"] == sel].iloc[0]
    st.download_button(
        f"⬇  Download  {row['filename']}", data=_wcs_bytes(int(sel)),
        file_name=row["filename"], mime="application/octet-stream",
        type="primary", use_container_width=True,
    )
    st.caption(f"Uploaded by **{row['uploaded_by'] or '—'}** on **{row['uploaded_at']}** · "
               f"{int(row['size_bytes'] / 1024):,} KB")
    if can_upload and st.button(f"🗑  Delete  {row['filename']}"):
        db.execute("DELETE FROM qc_wcs_docs WHERE id = :i", {"i": int(sel)})
        st.cache_data.clear()
        st.success(f"Deleted {row['filename']}.")
        st.rerun()


def page_inventory() -> None:
    st.header("Inventory")
    inv = db.query("SELECT * FROM inventory ORDER BY item_code")
    if "quantity" in inv.columns:
        inv["quantity"] = pd.to_numeric(inv["quantity"], errors="coerce")
    st.dataframe(inv, use_container_width=True, hide_index=True,
                 column_config=num2_cfg(inv))

    st.subheader("BOM vs inventory shortage")
    short = db.query(
        """
        WITH need AS (
            SELECT material_grade, part_name, item_code, description, size, sch_rating,
                   sum(quantity) AS qty_bom
            FROM bom
            WHERE lower(coalesce(status,'')) NOT IN ('issued','hold')
            GROUP BY 1,2,3,4,5,6
        )
        SELECT n.item_code, n.description, n.size, n.sch_rating,
               n.qty_bom,
               coalesce(sum(i.quantity),0) AS qty_stock,
               n.qty_bom - coalesce(sum(i.quantity),0) AS shortage
        FROM need n
        LEFT JOIN inventory i
          ON  coalesce(i.item_code,'')     = coalesce(n.item_code,'')
          AND coalesce(i.material_grade,'')= coalesce(n.material_grade,'')
          AND coalesce(i.size,'')          = coalesce(n.size,'')
          AND coalesce(i.sch_rating,'')    = coalesce(n.sch_rating,'')
        GROUP BY 1,2,3,4,5
        HAVING n.qty_bom - coalesce(sum(i.quantity),0) > 0
        ORDER BY shortage DESC
        """
    )
    for c in ("qty_bom", "qty_stock", "shortage"):
        if c in short.columns:
            short[c] = pd.to_numeric(short[c], errors="coerce")
    st.dataframe(short, use_container_width=True, hide_index=True,
                 column_config=num2_cfg(short))


# gated tab  ->  {checkbox label: permission token}
GATED_TABS = {
    "Targets & plan": {"Targets & plan": "Targets"},
    "Update progress": {"Fit-Up updates": "Update Fit-Up",
                        "Welding updates": "Update Welding"},
    "Scan & update (QR)": {"Shop-floor QR scan (this tab only)": "Field Scan"},
    "Delivery": {"Painting delivery": "Painting Delivery",
                 "Site delivery": "Site Delivery"},
    "Manpower": {"Manpower entry": "Manpower Report"},
    "Classify & export": {"Classify & export": "Generate Reports"},
    "QC WCS": {"QC WCS uploads": "QC WCS"},
    "Inventory": {"Inventory": "Inventory"},
}
_ALWAYS_TABS = [p for p, t in PAGE_PERMS.items()
                if not t and p not in ("Data admin", "Users")]


def _perm_to_areas(perm: str) -> str:
    if perm == "all":
        return "Full access"
    hits = [lbl for grp in GATED_TABS.values() for lbl, tok in grp.items()
            if tok in perm]
    return ", ".join(hits) if hits else "View only"


def page_users() -> None:
    st.header("Users & access")
    if st.session_state.get("permission") != "all":
        st.warning("Admin only (needs the 'all' permission).")
        return

    st.caption("Every user can open the view-only tabs ("
               + ", ".join(_ALWAYS_TABS)
               + "). The tabs below are the ones you can grant per user. "
               "Exception: an account with **only** the shop-floor QR scan "
               "grant sees the Scan & update tab and nothing else.")

    users = db.query(
        "SELECT username, password, permission FROM user_credentials ORDER BY username",
        ttl=0,
    )
    show_pw = st.checkbox("Show passwords", value=False)
    disp = users.assign(access=users["permission"].map(_perm_to_areas))
    if not show_pw:
        disp["password"] = "••••••"
    st.dataframe(disp[["username", "password", "access", "permission"]],
                 use_container_width=True, hide_index=True)

    st.subheader("Add / edit a user's access")
    pick = st.selectbox("User", ["＋ new user"] + list(users["username"]))
    editing = pick != "＋ new user"
    row = users[users["username"] == pick].iloc[0] if editing else None
    cur_perm = row["permission"] if editing else ""
    if editing:
        st.info(f"**{pick}** — current access: **{_perm_to_areas(cur_perm)}**  "
                f"(`{cur_perm}`)")

    with st.form("user_form"):
        c = st.columns(2)
        uname = c[0].text_input("Username", value=pick if editing else "",
                                disabled=editing)
        pw = c[1].text_input(
            "Password" + (" — leave blank to keep current" if editing else ""),
            value="", type="password",
        )
        full = st.checkbox("Full access (every tab)", value=(cur_perm == "all"),
                           key=f"full_{pick}")
        st.write("**Grant these tabs:**")
        chosen: list[str] = []
        for tab, grp in GATED_TABS.items():
            st.caption(tab)
            cols = st.columns(len(grp))
            for i, (lbl, tok) in enumerate(grp.items()):
                if cols[i].checkbox(lbl, value=(tok in cur_perm), disabled=full,
                                    key=f"perm_{pick}_{tok}"):
                    chosen.append(tok)
        saved = st.form_submit_button("Save", type="primary")

    if saved:
        uname_v = (pick if editing else uname).strip()
        final_pw = pw.strip() or (row["password"] if editing else "")
        if not uname_v:
            st.error("Username is required.")
        elif not final_pw:
            st.error("Password is required for a new user.")
        else:
            perm = "all" if full else (",".join(chosen) if chosen else "view-only")
            db.execute(
                """INSERT INTO user_credentials (username, password, permission)
                   VALUES (:u, :p, :perm)
                   ON CONFLICT (username) DO UPDATE
                     SET password = EXCLUDED.password, permission = EXCLUDED.permission""",
                {"u": uname_v, "p": final_pw, "perm": perm},
            )
            st.cache_data.clear()
            st.success(f"Saved '{uname_v}' — access: {_perm_to_areas(perm)}"
                       + ("" if pw.strip() or not editing else " (password unchanged)"))
            st.rerun()

    st.subheader("Delete a user")
    d1, d2 = st.columns([3, 1])
    victim = d1.selectbox("User", [u for u in users["username"]
                                   if u != st.session_state["user"]])
    if d2.button("🗑 Delete", disabled=not victim):
        db.execute("DELETE FROM user_credentials WHERE username = :u", {"u": victim})
        st.cache_data.clear()
        st.success(f"Deleted '{victim}'.")
        st.rerun()

    st.caption("Note: passwords are stored in plain text (same as the desktop app). "
               "Changes take effect at the user's next sign-in.")


def _split_activity(raw: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)\s*\[(.+)\]\s*$", str(raw or ""))
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return str(raw or "").strip(), "sign-in"


def page_activity() -> None:
    st.header("User activity")
    if st.session_state.get("permission") != "all":
        st.warning("Admin only (needs the 'all' permission).")
        return

    df = db.query(
        """SELECT id, username AS raw,
                  to_char(login_time AT TIME ZONE 'Asia/Kuala_Lumpur',
                          'YYYY-MM-DD HH24:MI:SS') AS ts,
                  (login_time AT TIME ZONE 'Asia/Kuala_Lumpur')::date AS d
           FROM user_log ORDER BY id DESC LIMIT 3000""",
        ttl=0,
    )
    if df.empty:
        st.info("No activity recorded yet.")
        return
    df[["user", "action"]] = df["raw"].apply(lambda r: pd.Series(_split_activity(r)))

    c = st.columns(3)
    c[0].metric("Events (last 3000)", f"{len(df):,}", border=True)
    c[1].metric("Distinct users", f"{df['user'].nunique():,}", border=True)
    c[2].metric("Sign-ins", f"{int((df['action'] == 'sign-in').sum()):,}", border=True)

    f = st.columns(3)
    fu = f[0].multiselect("User", sorted(df["user"].unique()))
    fa = f[1].multiselect("Action", sorted(df["action"].unique()))
    since = f[2].date_input("Since", value=None, format="YYYY-MM-DD")
    v = df
    if fu:
        v = v[v["user"].isin(fu)]
    if fa:
        v = v[v["action"].isin(fa)]
    if since:
        v = v[v["d"] >= since]

    st.subheader(f"Log ({len(v):,})")
    show_table(
        v[["ts", "user", "action"]].rename(columns={"ts": "when (MYT)"}),
        "user_activity",
    )

    st.subheader("Per user")
    summ = (df.groupby("user")
            .agg(events=("id", "count"),
                 sign_ins=("action", lambda s: int((s == "sign-in").sum())),
                 last_activity=("ts", "max"))
            .reset_index().sort_values("last_activity", ascending=False))
    st.dataframe(summ, use_container_width=True, hide_index=True)


_SNAP_PREFIX = "backup_spools_"


def page_admin() -> None:
    st.header("Data admin")
    if st.session_state.get("permission") != "all":
        st.warning("Admin only (needs the 'all' permission).")
        return
    _ensure_qr_schema()          # keep qr_id / fitup_by / welding_by in place

    eng = db.engine()
    from sqlalchemy import text as _t

    # ---------------- backup ----------------
    st.subheader("Backup")
    live = db.query("SELECT count(*) c FROM spools", ttl=0).iloc[0]["c"]
    st.caption(f"`spools` currently holds **{live:,}** rows.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📸 In-database snapshot of spools"):
            name = _SNAP_PREFIX + pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            with eng.begin() as cx:
                cx.execute(_t(f'CREATE TABLE public."{name}" AS SELECT * FROM public.spools'))
            st.success(f"Created snapshot table `{name}`.")
    with c2:
        tables = {
            t: db.query(f"SELECT * FROM {t}", ttl=0)
            for t in ["spools", "manpower_reports", "bom", "inventory",
                      "user_credentials", "user_log", "user_sessions"]
        }
        st.download_button(
            "⬇ Full backup workbook (.xlsx)",
            data=reports.build_full_backup_xlsx(tables),
            file_name=f"team_piping_backup_{reports.stamp()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    snaps = db.query(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema='public' AND table_name LIKE :p
           ORDER BY table_name DESC""",
        {"p": _SNAP_PREFIX + "%"}, ttl=0,
    )["table_name"].tolist()
    if snaps:
        st.write("**Existing snapshots**")
        pick = st.selectbox("Snapshot", snaps)
        n = db.query(f'SELECT count(*) c FROM public."{pick}"', ttl=0).iloc[0]["c"]
        cc1, cc2 = st.columns(2)
        if cc1.button(f"♻ Restore `{pick}` ({n:,} rows) into spools"):
            cols = db.query(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_schema='public' AND table_name='spools'
                     AND column_name <> 'id'
                   ORDER BY ordinal_position""", ttl=0,
            )["column_name"].tolist()
            collist = ", ".join(f'"{c}"' for c in cols)
            with eng.begin() as cx:
                cx.execute(_t("TRUNCATE public.spools RESTART IDENTITY"))
                cx.execute(_t(
                    f'INSERT INTO public.spools ({collist}) '
                    f'SELECT {collist} FROM public."{pick}"'
                ))
            st.cache_data.clear()
            st.success(f"Restored {n:,} rows from `{pick}`.")
        if cc2.button(f"🗑 Drop `{pick}`"):
            with eng.begin() as cx:
                cx.execute(_t(f'DROP TABLE public."{pick}"'))
            st.success(f"Dropped `{pick}`.")
            st.rerun()

    st.info("Supabase also keeps automated daily backups — dashboard → Database → Backups.")

    # ---------------- import ----------------
    st.divider()
    st.subheader("Import spools from Excel")
    st.caption("Master-format sheet (headers `WO NO`, `ISO DWG NO.`, …). "
               "This **replaces every row** in `spools`.")
    up = st.file_uploader("Excel file (.xlsx)", type=["xlsx"])
    if up is not None:
        raw = pd.read_excel(up, engine="openpyxl")
        clean, missing = reports.spools_df_from_excel(raw)
        st.write(f"File has **{len(raw):,}** rows → **{len(clean.columns)}** mapped columns.")
        if missing:
            st.warning(f"Headers not found (those columns import as blank): {', '.join(missing)}")
        st.dataframe(clean.head(20), use_container_width=True, hide_index=True)

        auto_snap = st.checkbox("Take an in-database snapshot first", value=True)
        confirm = st.checkbox(
            f"I understand this DELETES all {live:,} current rows and replaces them "
            f"with {len(clean):,} rows from this file"
        )
        if st.button("🚚 Replace spools now", type="primary", disabled=not confirm):
            has_qr = not db.query(
                "SELECT 1 FROM information_schema.columns WHERE table_schema='public' "
                "AND table_name='spools' AND column_name='qr_id'", ttl=0,
            ).empty
            relinked = names_kept = 0
            with eng.begin() as cx:
                if auto_snap:
                    sname = _SNAP_PREFIX + pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                    cx.execute(_t(f'CREATE TABLE public."{sname}" AS SELECT * FROM public.spools'))
                _kk = ("iso_dwg_no", "line_no", "iso_run_no", "dwg_spool_no")
                _jk = _kk + ("joint_no",)
                if has_qr:
                    # carry printed spool QR codes over the re-import, by spool key
                    cx.execute(_t(
                        "CREATE TEMP TABLE _qr_keep ON COMMIT DROP AS "
                        f"SELECT DISTINCT {', '.join(_kk)}, qr_id "
                        "FROM public.spools WHERE coalesce(qr_id,'') <> ''"
                    ))
                    # and the fitter / welder names, by joint key
                    cx.execute(_t(
                        "CREATE TEMP TABLE _by_keep ON COMMIT DROP AS "
                        f"SELECT DISTINCT {', '.join(_jk)}, fitup_by, welding_by "
                        "FROM public.spools "
                        "WHERE coalesce(fitup_by,'')<>'' OR coalesce(welding_by,'')<>''"
                    ))
                cx.execute(_t("TRUNCATE public.spools RESTART IDENTITY"))
                clean.to_sql("spools", cx, if_exists="append", index=False,
                             chunksize=1000, method="multi")
                if has_qr:
                    _m = " AND ".join(
                        f"coalesce(s.{c},'') = coalesce(k.{c},'')" for c in _kk)
                    relinked = cx.execute(_t(
                        "UPDATE public.spools s SET qr_id = k.qr_id "
                        f"FROM _qr_keep k WHERE s.qr_id IS NULL AND {_m}"
                    )).rowcount
                    _mj = " AND ".join(
                        f"coalesce(s.{c},'') = coalesce(k.{c},'')" for c in _jk)
                    names_kept = cx.execute(_t(
                        "UPDATE public.spools s "
                        "SET fitup_by = k.fitup_by, welding_by = k.welding_by "
                        f"FROM _by_keep k WHERE {_mj}"
                    )).rowcount
            try:
                db.execute("INSERT INTO user_log (username) VALUES (:u)",
                           {"u": f"{st.session_state['user']} [excel import {len(clean)} rows]"})
            except Exception:
                pass
            st.cache_data.clear()
            st.success(f"Imported {len(clean):,} rows into spools"
                       + (f"; snapshot `{sname}` kept." if auto_snap else ".")
                       + (f" Re-linked {relinked:,} QR code(s)." if relinked else "")
                       + (f" Kept {names_kept:,} fitter/welder name(s)." if names_kept else ""))


def page_manpower() -> None:
    st.header("Manpower reports")
    perm = st.session_state.get("permission", "")
    can_edit = perm == "all" or "Manpower Report" in perm

    if can_edit:
        st.subheader("Add / update a day")
        with st.form("mp"):
            c = st.columns(3)
            d = c[0].date_input("Date", value=date.today(), format="YYYY-MM-DD")
            w = c[1].number_input("Total welders", min_value=0, step=1, value=0)
            fi = c[2].number_input("Total fitters", min_value=0, step=1, value=0)
            saved = st.form_submit_button("Save", type="primary")
        if saved:
            db.execute(
                """INSERT INTO manpower_reports (date, total_welders, total_fitters)
                   VALUES (:d, :w, :f)
                   ON CONFLICT (date) DO UPDATE
                     SET total_welders = EXCLUDED.total_welders,
                         total_fitters = EXCLUDED.total_fitters""",
                {"d": d.isoformat(), "w": int(w), "f": int(fi)},
            )
            st.cache_data.clear()
            st.success(f"Saved manpower for {d.isoformat()}.")
            st.rerun()
    else:
        st.caption("View only — needs the 'Manpower Report' permission to edit.")

    df = db.query(
        "SELECT date, total_welders, total_fitters, "
        "coalesce(total_welders,0)+coalesce(total_fitters,0) AS total "
        "FROM manpower_reports ORDER BY date DESC",
        ttl=0,
    )
    st.subheader("Records")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        chart = df.copy()
        chart["date"] = pd.to_datetime(chart["date"], errors="coerce")
        st.line_chart(chart.set_index("date")[["total_welders", "total_fitters"]])

    if can_edit and not df.empty:
        c1, c2 = st.columns([3, 1])
        target = c1.selectbox("Delete a record", df["date"].tolist())
        if c2.button("🗑 Delete", disabled=not target):
            db.execute("DELETE FROM manpower_reports WHERE date = :d", {"d": target})
            st.cache_data.clear()
            st.success(f"Deleted {target}.")
            st.rerun()


{
    "Overview": page_overview,
    "Targets & plan": page_targets,
    "Work order summary": page_wo_summary,
    "Update progress": page_update,
    "Scan & update": page_scan,
    "Field workers": page_field_workers,
    "QR labels": page_qr_labels,
    "Delivery": page_delivery,
    "Spools": page_spools,
    "Classify & export": page_reports,
    "QC WCS": page_qc_wcs,
    "Inventory": page_inventory,
    "Manpower": page_manpower,
    "Activity": page_activity,
    "Data admin": page_admin,
    "Users": page_users,
}[page]()
