"""Supabase (Postgres) access layer for the Streamlit frontend.

Connects server-side through SQLAlchemy using the connection string in
.streamlit/secrets.toml ([connections.supabase] url = ...). Because the
connection uses the postgres/service credentials it bypasses RLS, so the
service credentials must never reach the browser - keep them in secrets.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import text


DEFAULT_CONN = "supabase"


def project_list() -> dict:
    """{display name: connection name} from secrets `[projects]`.
    Empty -> single-project deployment (everything uses `supabase`)."""
    try:
        return {str(k): str(v) for k, v in dict(st.secrets.get("projects", {})).items()}
    except Exception:
        return {}


def _conn_name() -> str:
    return st.session_state.get("conn_name", DEFAULT_CONN)


@st.cache_resource
def _conn_for(name: str):
    # Streamlit's SQLConnection: pools, reconnects, reads [connections.<name>].
    return st.connection(name, type="sql")


def _conn():
    return _conn_for(_conn_name())


def query(sql: str, params: dict | None = None, ttl: int = 60) -> pd.DataFrame:
    """Read query -> DataFrame (cached for `ttl` seconds)."""
    return _conn().query(sql, params=params or {}, ttl=ttl)


def engine():
    """Raw SQLAlchemy engine, for bulk loads / DDL."""
    return _conn().engine


def execute(sql: str, params: dict | None = None) -> None:
    """Write query (INSERT/UPDATE/DELETE), committed."""
    with _conn().session as s:
        s.execute(text(sql), params or {})
        s.commit()


def execute_many(sql: str, param_list: list[dict]) -> None:
    """Run the same write once per param dict, all in one transaction."""
    with _conn().session as s:
        for p in param_list:
            s.execute(text(sql), p)
        s.commit()


def write(sql: str, params: dict | None = None) -> int:
    """Write query; returns the number of rows affected."""
    with _conn().session as s:
        r = s.execute(text(sql), params or {})
        s.commit()
        return r.rowcount


def transaction(steps: list[tuple[str, dict]]) -> list[int]:
    """Run several writes in ONE transaction. Returns each step's rowcount.
    Any error rolls the whole thing back and propagates (e.g. a unique
    constraint -> sqlalchemy.exc.IntegrityError)."""
    out: list[int] = []
    with _conn().session as s:
        for sql, p in steps:
            out.append(s.execute(text(sql), p or {}).rowcount)
        s.commit()
    return out


# ------------------------------------------------------------------ auth
def check_login(username: str, password: str) -> str | None:
    """Return the permission string on success, else None.

    Matches the current SQLite app's plaintext scheme. Swap for Supabase
    Auth or password hashing when ready.
    """
    df = query(
        "SELECT password, permission FROM user_credentials WHERE username = :u",
        {"u": username},
        ttl=0,
    )
    if df.empty or str(df.iloc[0]["password"]) != str(password):
        return None
    return df.iloc[0]["permission"]


def log_login(username: str) -> None:
    execute("INSERT INTO user_log (username) VALUES (:u)", {"u": username})


# ------------------------------------------------------------ settings
_SETTINGS_DDL = """
CREATE TABLE IF NOT EXISTS project_settings (
    key        text PRIMARY KEY,
    value      text,
    updated_at timestamptz NOT NULL DEFAULT now()
)
"""


def get_settings() -> dict:
    try:
        df = query("SELECT key, value FROM project_settings", ttl=0)
        return dict(zip(df["key"], df["value"]))
    except Exception:
        return {}


def set_settings(values: dict) -> None:
    with _conn().session as s:
        s.execute(text(_SETTINGS_DDL))
        for k, v in values.items():
            s.execute(
                text("""INSERT INTO project_settings (key, value) VALUES (:k, :v)
                        ON CONFLICT (key) DO UPDATE
                          SET value = EXCLUDED.value, updated_at = now()"""),
                {"k": k, "v": None if v is None else str(v)},
            )
        s.commit()
