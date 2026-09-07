"""
Migrate the local SQLite data into Supabase (PostgreSQL).

Reads:
    database/spool_tracking.db    -> spools, manpower_reports,
                                     user_credentials, user_log, user_sessions
    database/material_tracking.db -> bom, inventory

Writes to whatever Postgres the DATABASE_URL points at (your Supabase project).

------------------------------------------------------------------
Setup
------------------------------------------------------------------
1. pip install -r supabase/requirements.txt
2. Apply supabase/schema.sql first (Supabase Dashboard -> SQL Editor).
3. Get the connection string:
     Supabase Dashboard -> Project Settings -> Database -> Connection string
     -> "URI" (use the direct connection, port 5432; the transaction
     pooler on 6543 also works for this one-shot load).
   It looks like:
     postgresql://postgres:[PASSWORD]@db.<ref>.supabase.co:5432/postgres
4. Put it in an environment variable or a .env file next to this script:
     DATABASE_URL=postgresql://postgres:...@db.<ref>.supabase.co:5432/postgres

------------------------------------------------------------------
Run
------------------------------------------------------------------
    python supabase/migrate_from_sqlite.py                 # insert everything
    python supabase/migrate_from_sqlite.py --truncate      # wipe target tables first (recommended for re-runs)
    python supabase/migrate_from_sqlite.py --only spools   # one table
    python supabase/migrate_from_sqlite.py --dry-run       # read + report, no writes
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:  # optional
    load_dotenv = None

# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPOOL_DB = PROJECT_ROOT / "database" / "spool_tracking.db"
MATERIAL_DB = PROJECT_ROOT / "database" / "material_tracking.db"

# sqlite table  ->  (sqlite db path, target postgres table)
TABLE_MAP = {
    "spools":           (SPOOL_DB,    "spools"),
    "manpower_reports": (SPOOL_DB,    "manpower_reports"),
    "user_credentials": (SPOOL_DB,    "user_credentials"),
    "user_log":         (SPOOL_DB,    "user_log"),
    "user_sessions":    (SPOOL_DB,    "user_sessions"),
    "bom":              (MATERIAL_DB, "bom"),
    "inventory":        (MATERIAL_DB, "inventory"),
}

# load order does not matter (no foreign keys), but keep it readable
LOAD_ORDER = [
    "user_credentials", "user_log", "user_sessions",
    "manpower_reports", "bom", "inventory", "spools",
]

CHUNK = 1000


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def get_database_url() -> str:
    if load_dotenv:
        load_dotenv(PROJECT_ROOT / "supabase" / ".env")
        load_dotenv(PROJECT_ROOT / ".env")
    url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not url:
        sys.exit(
            "ERROR: set DATABASE_URL (Supabase -> Project Settings -> Database "
            "-> Connection string -> URI) in the environment or in supabase/.env"
        )
    return url


def pg_columns(cur, table: str) -> dict[str, str]:
    """{column_name: data_type} for a target table, excluding identity/default-managed audit cols."""
    cur.execute(
        """
        SELECT column_name, data_type, is_identity
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    cols = {}
    for name, dtype, is_identity in cur.fetchall():
        if is_identity == "YES":
            continue
        if name in ("created_at", "updated_at"):
            continue  # let DB defaults / triggers handle these
        cols[name] = dtype
    return cols


def coerce(df: pd.DataFrame, coltypes: dict[str, str]) -> pd.DataFrame:
    """Align a sqlite dataframe to the target columns and clean values."""
    keep = [c for c in df.columns if c in coltypes]
    missing = [c for c in coltypes if c not in df.columns]
    df = df[keep].copy()

    for col in keep:
        dtype = coltypes[col]
        if dtype in ("numeric", "integer", "bigint", "double precision", "real"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if dtype in ("integer", "bigint"):
                df[col] = df[col].astype("Int64")
        else:
            # text: normalise NaN/None to real None, keep "" as ""
            df[col] = df[col].where(pd.notna(df[col]), None)

    # replace pandas NA/NaN with None everywhere for psycopg2
    df = df.astype(object).where(pd.notna(df), None)
    return df, missing


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Migrate SQLite -> Supabase/Postgres")
    ap.add_argument("--truncate", action="store_true",
                    help="TRUNCATE each target table before loading (RESTART IDENTITY CASCADE)")
    ap.add_argument("--only", metavar="TABLE", help="migrate a single table only")
    ap.add_argument("--dry-run", action="store_true", help="read and report, write nothing")
    args = ap.parse_args()

    tables = [args.only] if args.only else LOAD_ORDER
    for t in tables:
        if t not in TABLE_MAP:
            sys.exit(f"unknown table '{t}'. known: {', '.join(TABLE_MAP)}")

    conn = None
    execute_values = None
    if not args.dry_run:
        try:
            import psycopg2
            from psycopg2.extras import execute_values
        except ImportError:
            sys.exit("ERROR: psycopg2 not installed. Run: "
                     "python -m pip install -r supabase/requirements.txt")
        conn = psycopg2.connect(get_database_url())
        conn.autocommit = False

    grand_total = 0
    try:
        for name in tables:
            sqlite_path, target = TABLE_MAP[name]
            if not Path(sqlite_path).exists():
                print(f"[skip] {name}: {sqlite_path} not found")
                continue

            with sqlite3.connect(sqlite_path) as sconn:
                df = pd.read_sql_query(f'SELECT * FROM "{name}"', sconn)
            print(f"\n=== {name} -> public.{target}  ({len(df)} rows in SQLite) ===")

            if args.dry_run:
                print(f"    columns: {list(df.columns)}")
                grand_total += len(df)
                continue

            with conn.cursor() as cur:
                coltypes = pg_columns(cur, target)
                if not coltypes:
                    print(f"    !! target table public.{target} has no columns / does not exist. "
                          f"Run supabase/schema.sql first.")
                    continue

                src_cols = list(df.columns)
                df, missing = coerce(df, coltypes)
                if missing:
                    print(f"    note: target columns with no SQLite source (left to default): {missing}")
                extra = [c for c in src_cols if c not in coltypes]
                if extra:
                    print(f"    note: SQLite columns not in target (ignored): {extra}")

                if args.truncate:
                    cur.execute(f'TRUNCATE TABLE public.{target} RESTART IDENTITY CASCADE')
                    print(f"    truncated public.{target}")

                cols = list(df.columns)
                collist = ", ".join(f'"{c}"' for c in cols)
                rows = list(df.itertuples(index=False, name=None))
                inserted = 0
                for i in range(0, len(rows), CHUNK):
                    batch = rows[i:i + CHUNK]
                    execute_values(
                        cur,
                        f'INSERT INTO public.{target} ({collist}) VALUES %s',
                        batch,
                    )
                    inserted += len(batch)
                    print(f"    inserted {inserted}/{len(rows)}", end="\r")
                print(f"    inserted {inserted}/{len(rows)} rows            ")
                grand_total += inserted

        if conn:
            conn.commit()
            print(f"\nCommitted. Total rows inserted: {grand_total}")
        else:
            print(f"\nDry run complete. Rows that would be read: {grand_total}")
    except Exception:
        if conn:
            conn.rollback()
            print("\nRolled back - nothing was written.")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
