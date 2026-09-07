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
import math
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import db
import reports

_LOGO_PATH = Path(__file__).parent / "assets" / "naec_logo.jpg"
try:
    LOGO_URI = "data:image/jpeg;base64," + base64.b64encode(
        _LOGO_PATH.read_bytes()).decode()
except Exception:
    LOGO_URI = ""

_PCT = dict(min_value=0, max_value=100, format="%.0f%%")


def show_table(df: pd.DataFrame, name: str, *, progress: tuple = (),
               money: tuple = (), styler=None, height: int | None = None) -> None:
    """A dataframe with formatted / progress columns and a CSV download."""
    cfg = {c: st.column_config.ProgressColumn(c.replace("_", " "), **_PCT)
           for c in progress if c in df.columns}
    cfg.update({c: st.column_config.NumberColumn(c.replace("_", " "), format="%.2f")
                for c in money if c in df.columns})
    kw = {"height": height} if height is not None else {}
    st.dataframe(styler if styler is not None else df, use_container_width=True,
                 hide_index=True, column_config=cfg, **kw)
    st.download_button("⬇ CSV", df.to_csv(index=False).encode(),
                       file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}")


_ALT_AXIS = "#9fb0c9"


def dark_alt(chart):
    """Make an Altair chart legible on the dark theme (call once, at render)."""
    return (
        chart.configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=_ALT_AXIS, titleColor=_ALT_AXIS,
                        gridColor="#26344c", domainColor="#26344c")
        .configure_legend(labelColor=_ALT_AXIS, titleColor=_ALT_AXIS)
        .configure_title(color="#e2e8f0")
    )


def donut(done: float, total: float, color: str = "#22c55e"):
    pct = (done / total * 100) if total else 0
    src = pd.DataFrame({"cat": ["done", "remaining"],
                        "val": [done, max(total - done, 0.0)]})
    arc = (
        alt.Chart(src).mark_arc(innerRadius=48, outerRadius=72)
        .encode(theta=alt.Theta("val:Q", stack=True),
                color=alt.Color("cat:N", legend=None,
                                scale=alt.Scale(domain=["done", "remaining"],
                                                range=[color, "#2b3a52"])),
                tooltip=[alt.Tooltip("cat:N", title=""),
                         alt.Tooltip("val:Q", title="dia-inch", format=",.1f")])
    )
    text = (alt.Chart(pd.DataFrame({"t": [f"{pct:.0f}%"]}))
            .mark_text(size=22, fontWeight="bold", color="#e2e8f0").encode(text="t:N"))
    return (arc + text).properties(height=180)


def donut_block(col, label: str, done: float, total: float, color: str) -> None:
    col.markdown(
        f"<div style='text-align:center;line-height:1.25'>"
        f"<b>{label}</b><br>"
        f"<span style='color:#94a3b8;font-size:0.85em'>"
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
    f"<div style='font-size:1.7rem;font-weight:800;color:#f1f5f9'>"
    f"{_PIPE_SVG}Team Piping</div>"
    "<div style='font-size:.72rem;font-weight:700;letter-spacing:.16em;"
    "color:#4d8dff;margin-top:3px'>NAEC MALAYSIA SDN BHD</div></div>"
)

PAGE_ICONS = {
    "Overview": "📊", "Targets & plan": "🎯", "Work order summary": "📋",
    "Update progress": "✏️", "Delivery": "🚚", "Spools": "🔩",
    "Classify & export": "🗂️", "Inventory": "📦", "Manpower": "👷",
    "Data admin": "🛠️", "Users": "👥",
}


def inject_css() -> None:
    # Dark theme. The app's base (page bg, text, dataframe grid) comes from
    # .streamlit/config.toml (base = "dark"); this only adds the accents,
    # glass sidebar and card styling. Viewers can switch to light via
    # the ⋮ menu → Settings → Theme.
    st.markdown(
        """
<style>
:root { --accent:#4d8dff; --accent2:#22c55e; --ink:#f1f5f9; --line:#2b3a52; }
.block-container { padding-top: 2rem; max-width: 1320px; position:relative; z-index:1; }
section[data-testid="stSidebar"] { z-index:2; }
/* inputs — keep visible on the dark theme */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTextArea textarea, [data-baseweb="input"], [data-baseweb="select"] > div,
[data-baseweb="textarea"] {
  background:#0f1a2e !important; color:#e6edf7 !important;
  border:1px solid #35507a !important; border-radius:8px !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color:#7a8db0 !important; }
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border-color:var(--accent) !important;
}
h1 { font-weight:700; letter-spacing:-.01em; color:var(--ink); }
h2 { margin-top:.3rem; padding-bottom:.35rem; border-bottom:2px solid var(--line);
     color:var(--ink); }
h3 { color:var(--accent); font-weight:600; }
/* --- frosted-glass sidebar --- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#152036 0%,#111a2e 55%,#161327 100%);
  border-right: 1px solid rgba(255,255,255,.06);
}
section[data-testid="stSidebar"] .stButton>button {
  background: rgba(255,255,255,.06);
  -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 2px 14px rgba(0,0,0,.35);
  border-radius: 12px; color: var(--ink);
}
section[data-testid="stSidebar"] .stButton>button:hover {
  background: rgba(77,141,255,.18); border-color: var(--accent); color:#cfe0ff;
}
section[data-testid="stSidebar"] [role="radiogroup"] > label {
  background: rgba(255,255,255,.045);
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 1px 8px rgba(0,0,0,.3);
  border-radius: 11px;
  padding: .5rem .7rem !important;
  margin-bottom: 6px;
  transition: background .15s ease, border-color .15s ease, box-shadow .15s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
  background: rgba(255,255,255,.09);
}
section[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
  background: rgba(77,141,255,.20);
  border-color: rgba(77,141,255,.55);
  box-shadow: 0 2px 16px rgba(77,141,255,.22);
}
section[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {
  display: none;               /* hide radio dot for a clean pill */
}
div[data-testid="stMetric"] {
  background:#1a2436; border:1px solid var(--line); border-left:4px solid var(--accent);
  border-radius:12px; padding:14px 16px;
}
div[data-testid="stMetric"] label p { color:#94a3b8; font-weight:500; }
.stButton>button, .stDownloadButton>button, .stForm button {
  border-radius:9px; font-weight:600;
}
.stDownloadButton>button {
  padding:.7rem 1.1rem; font-size:1rem; min-height:3rem;
}
.stDownloadButton>button[kind="primary"] { box-shadow:0 4px 16px rgba(77,141,255,.28); }
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
  border:1px solid var(--line); border-radius:10px;
}
.stTabs [data-baseweb="tab-list"] { gap:2px; }
.stTabs [aria-selected="true"] { color:var(--accent) !important; }
div[data-testid="stAlert"] { border-radius:10px; }
[data-testid="stProgress"] > div > div > div { background:var(--accent2); }
hr { margin:1rem 0; border-color:var(--line); }
</style>
""",
        unsafe_allow_html=True,
    )
    if LOGO_URI:
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
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        if LOGO_URI:
            st.markdown(
                f"<div style='text-align:center;margin:1.2rem 0 .4rem'>"
                f"<img src='{LOGO_URI}' style='width:230px;background:#fff;"
                f"padding:16px 20px;border-radius:18px;"
                f"box-shadow:0 8px 30px rgba(0,0,0,.35)'></div>",
                unsafe_allow_html=True,
            )
        st.markdown(f"<div style='text-align:center'>{BRAND_HTML}</div>",
                    unsafe_allow_html=True)
        st.subheader("Sign in")
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Sign in", use_container_width=True)
    if ok:
        perm = db.check_login(u.strip(), p)
        if perm is None:
            st.error("Invalid username or password.")
        else:
            st.session_state["user"] = u.strip()
            st.session_state["permission"] = perm
            try:
                db.log_login(u.strip())
            except Exception:
                pass
            st.rerun()
    st.stop()


inject_css()
login_gate()

# ---- access control -------------------------------------------------
# Permission tokens recognised by the app. A user's `permission` string in
# user_credentials is a comma-separated list of these (or the literal 'all').
KNOWN_TOKENS = [
    "all", "Spools", "Project Summary", "Targets", "Update Fit-Up", "Update Welding",
    "Painting Delivery", "Site Delivery", "Generate Reports", "Inventory",
    "Manpower Report",
]
ADMIN = "__admin__"   # page tokens that only 'all' can satisfy

# page -> tokens that grant it. [] = every signed-in user (read-only views).
# Data-entry and admin pages are gated; the plan/report views stay open.
PAGE_PERMS = {
    "Overview": [],
    "Targets & plan": ["Targets"],
    "Work order summary": [],
    "Update progress": ["Update Fit-Up", "Update Welding"],
    "Delivery": ["Painting Delivery", "Site Delivery"],
    "Spools": [],
    "Classify & export": ["Generate Reports"],
    "Inventory": ["Inventory"],
    "Manpower": ["Manpower Report"],
    "Data admin": [ADMIN],
    "Users": [ADMIN],
}


def can_see(page: str, perm: str) -> bool:
    if perm == "all":
        return True
    toks = PAGE_PERMS.get(page, [])
    if not toks:
        return True
    if ADMIN in toks:
        return False
    return any(t in perm for t in toks)


with st.sidebar:
    st.markdown(BRAND_HTML, unsafe_allow_html=True)
    st.caption(f"Signed in as **{st.session_state['user']}**")
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    _perm = st.session_state.get("permission", "")
    visible = [p for p in PAGE_PERMS if can_see(p, _perm)] or ["Overview"]
    page = st.radio("Page", visible, label_visibility="collapsed",
                    format_func=lambda p: f"{PAGE_ICONS.get(p, '•')}  {p}")

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
             AND substr(site_delivery_date,1,10) <= :asof, false))        AS delivered
    FROM spools
    WHERE shop_field='S'
    GROUP BY iso_dwg_no, line_no, iso_run_no, dwg_spool_no
)
SELECT
  (SELECT count(*) FROM sp)                          AS total_spools,
  (SELECT count(*) FROM sp WHERE welded)             AS completed_spools,
  (SELECT count(*) FROM sp WHERE delivered)          AS delivered_spools,
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
       AND substr(site_delivery_date,1,10) <= :asof)                                          AS delivered_di
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
    r1 = st.columns(5)
    r1[0].metric("Total shop dia-inch", f(s["shop_di"]), border=True)
    r1[1].metric("Total field dia-inch", f(s["field_di"]), border=True)
    r1[2].metric("Work order issued", f"{int(s['wo_issued'] or 0):,}", border=True)
    r1[3].metric("WO total dia-inch", f(s["wo_total_di"]), border=True)
    r1[4].metric("WO fit-up balance", f(s["wo_fitup_bal"]), border=True)

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
    r4 = st.columns(3)
    r4[0].metric("Total pipe spools", f"{tsp:,}", border=True)
    r4[1].metric("Total completed spools", f"{csp:,}",
                 f"{csp/tsp*100:.0f}%" if tsp else None, delta_color="off", border=True)
    r4[2].metric("Total delivered spools", f"{dsp:,}",
                 f"{dsp/tsp*100:.0f}%" if tsp else None, delta_color="off", border=True)

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
            GROUP BY 1 ORDER BY dia_inch DESC
            """,
            {"asof": asof.isoformat()}, ttl=30,
        )
        for cc in ("joints", "dia_inch", "fitup_di", "welding_di"):
            d[cc] = d[cc].astype(float)
        di = d["dia_inch"].where(d["dia_inch"] > 0)
        d["fitup_%"] = (d["fitup_di"] / di * 100).round(1).fillna(0)
        d["welding_%"] = (d["welding_di"] / di * 100).round(1).fillna(0)
        return d

    st.subheader("Breakdown")
    t1, t2 = st.tabs(["By batch no", "By area"])
    with t1:
        show_table(breakdown("batch_no"), "progress_by_batch",
                   progress=("fitup_%", "welding_%"),
                   money=("dia_inch", "fitup_di", "welding_di"))
    with t2:
        show_table(breakdown("area"), "progress_by_area",
                   progress=("fitup_%", "welding_%"),
                   money=("dia_inch", "fitup_di", "welding_di"))


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
    d_rest = [int(x) for x in (cfg.get("rest") or "6").split(",") if x != ""]
    d_hol_text = "\n".join((cfg.get("holidays") or "").split(","))

    with st.form("plan"):
        c = st.columns(4)
        plan_start = c[0].date_input("Plan start", value=d_start, format="YYYY-MM-DD")
        target_date = c[1].date_input("Target completion", value=d_target, format="YYYY-MM-DD")
        scope = c[2].selectbox(
            "Scope", ["issued", "all"], index=0 if d_scope == "issued" else 1,
            format_func=lambda v: "Issued work orders" if v == "issued" else "All shop",
        )
        rest = c[3].multiselect("Weekly rest days", options=list(range(7)), default=d_rest,
                                format_func=lambda i: _WD[i])
        hol_text = st.text_area(
            "Public holidays (one date per line, YYYY-MM-DD)",
            value=d_hol_text, height=120,
            placeholder="2025-08-31\n2025-09-16",
        )
        if st.form_submit_button("Save plan", type="primary", disabled=not can_edit):
            hol_set, bad = _parse_dates(hol_text)
            if bad:
                st.error(f"Not valid dates, fix and re-save: {', '.join(bad)}")
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
    planned_per_day = scope_di / total_wd if total_wd else 0.0

    if target_date < today:
        st.warning(f"Target date {target_date.isoformat()} is in the past.")
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
    st.subheader("Plan vs actual")
    st.dataframe(
        rep.style.map(
            lambda v: "color:#f87171;font-weight:bold" if v == "BEHIND" else "color:#34d399",
            subset=["Status"],
        ),
        use_container_width=True, hide_index=True,
    )
    b = st.columns(2)
    for i, r in rep.iterrows():
        b[i].metric(f"{r['Discipline']} delay qty (dia-inch)", f"{r['Delay qty']:,.2f}",
                    r["Status"], delta_color="inverse")

    end = max(target_date, today)
    idx = pd.date_range(plan_start, end, freq="D")
    for name, (sdf, ppd) in charts.items():
        with st.expander(f"{name}: planned vs actual cumulative"):
            act = (sdf.assign(dt=pd.to_datetime(sdf["dt"])).set_index("dt")["di"]
                   .reindex(idx, fill_value=0).cumsum())
            planned = [min(ppd * _wdays(plan_start, min(x.date(), target_date), rest_s, hol_s),
                           scope_di) for x in idx]
            st.line_chart(pd.DataFrame({"Planned": planned, "Actual": act.values}, index=idx))


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
    st.dataframe(totals, use_container_width=True, hide_index=True)

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

    joints = db.query(
        f"""SELECT joint_no, joint_size, item_1, sch_rating_1, item_2, sch_rating_2,
                   coalesce(fitup_date,'')   AS fitup_date,
                   coalesce(welding_date,'') AS welding_date
            {base} AND iso_dwg_no=:i AND line_no=:l AND iso_run_no=:p AND dwg_spool_no=:s
            ORDER BY joint_no""",
        {"i": iso, "l": line, "p": pageno, "s": spool}, ttl=0,
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
               fitup_date, welding_date, painting_date, delivery_date,
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
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.bar_chart(summary.set_index("Spool Status")["Total_Spools"])

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


def page_inventory() -> None:
    st.header("Inventory")
    inv = db.query("SELECT * FROM inventory ORDER BY item_code")
    st.dataframe(inv, use_container_width=True, hide_index=True)

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
    st.dataframe(short, use_container_width=True, hide_index=True)


# gated tab  ->  {checkbox label: permission token}
GATED_TABS = {
    "Targets & plan": {"Targets & plan": "Targets"},
    "Update progress": {"Fit-Up updates": "Update Fit-Up",
                        "Welding updates": "Update Welding"},
    "Delivery": {"Painting delivery": "Painting Delivery",
                 "Site delivery": "Site Delivery"},
    "Manpower": {"Manpower entry": "Manpower Report"},
    "Classify & export": {"Classify & export": "Generate Reports"},
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
               + "). The tabs below are the ones you can grant per user.")

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

    st.subheader("Add / update a user")
    pick = st.selectbox("User", ["＋ new user"] + list(users["username"]))
    editing = pick != "＋ new user"
    row = users[users["username"] == pick].iloc[0] if editing else None
    cur_perm = row["permission"] if editing else ""

    with st.form("user_form"):
        c = st.columns(2)
        uname = c[0].text_input("Username", value=pick if editing else "",
                                disabled=editing)
        pw = c[1].text_input("Password", value=row["password"] if editing else "")
        full = st.checkbox("Full access (every tab)", value=(cur_perm == "all"))
        st.write("**Grant these tabs:**")
        chosen: list[str] = []
        for tab, grp in GATED_TABS.items():
            st.caption(tab)
            cols = st.columns(len(grp))
            for i, (lbl, tok) in enumerate(grp.items()):
                if cols[i].checkbox(lbl, value=(tok in cur_perm), disabled=full,
                                    key=f"perm_{pick}_{tok}"):
                    chosen.append(tok)
        saved = st.form_submit_button("Save user", type="primary")

    if saved:
        uname_v = (pick if editing else uname).strip()
        if not uname_v or not pw.strip():
            st.error("Username and password are required.")
        else:
            perm = "all" if full else (",".join(chosen) if chosen else "view-only")
            db.execute(
                """INSERT INTO user_credentials (username, password, permission)
                   VALUES (:u, :p, :perm)
                   ON CONFLICT (username) DO UPDATE
                     SET password = EXCLUDED.password, permission = EXCLUDED.permission""",
                {"u": uname_v, "p": pw.strip(), "perm": perm},
            )
            st.cache_data.clear()
            st.success(f"Saved '{uname_v}' — {_perm_to_areas(perm)}")
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


_SNAP_PREFIX = "backup_spools_"


def page_admin() -> None:
    st.header("Data admin")
    if st.session_state.get("permission") != "all":
        st.warning("Admin only (needs the 'all' permission).")
        return

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
            with eng.begin() as cx:
                if auto_snap:
                    sname = _SNAP_PREFIX + pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                    cx.execute(_t(f'CREATE TABLE public."{sname}" AS SELECT * FROM public.spools'))
                cx.execute(_t("TRUNCATE public.spools RESTART IDENTITY"))
                clean.to_sql("spools", cx, if_exists="append", index=False,
                             chunksize=1000, method="multi")
            try:
                db.execute("INSERT INTO user_log (username) VALUES (:u)",
                           {"u": f"{st.session_state['user']} [excel import {len(clean)} rows]"})
            except Exception:
                pass
            st.cache_data.clear()
            st.success(f"Imported {len(clean):,} rows into spools"
                       + (f"; snapshot `{sname}` kept." if auto_snap else "."))


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
    "Delivery": page_delivery,
    "Spools": page_spools,
    "Classify & export": page_reports,
    "Inventory": page_inventory,
    "Manpower": page_manpower,
    "Data admin": page_admin,
    "Users": page_users,
}[page]()
