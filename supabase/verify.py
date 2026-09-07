"""Quick check that the migrated data is in Supabase."""
import os, sys
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass
import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit("set DATABASE_URL in supabase/.env")

conn = psycopg2.connect(url)
cur = conn.cursor()
for t in ["spools", "manpower_reports", "user_credentials", "user_log",
          "user_sessions", "bom", "inventory"]:
    cur.execute(f"SELECT count(*) FROM public.{t}")
    print(f"{t:20s} {cur.fetchone()[0]:>6}")
print("-" * 28)
cur.execute("""
    SELECT count(*) FILTER (WHERE coalesce(fitup_date,'')    <> '') AS fitted,
           count(*) FILTER (WHERE coalesce(welding_date,'')  <> '') AS welded,
           count(*) FILTER (WHERE coalesce(delivery_date,'') <> '') AS delivered
    FROM public.spools
""")
f, w, d = cur.fetchone()
print(f"spools fitted={f}  welded={w}  delivered={d}")
conn.close()
