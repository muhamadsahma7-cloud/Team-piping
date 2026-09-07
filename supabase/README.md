# Online database for Team Piping (Supabase)

This moves the two local SQLite files to a hosted PostgreSQL database on
Supabase, so the data lives online and multiple users / a Streamlit app
can reach it.

| Local file | Tables | Now in Supabase |
|---|---|---|
| `database/spool_tracking.db` | `spools`, `manpower_reports`, `user_credentials`, `user_log`, `user_sessions` | same names, schema `public` |
| `database/material_tracking.db` | `bom`, `inventory` | same names, schema `public` |

Files here:

- `schema.sql` — creates every table, index, `updated_at` trigger, and turns on RLS.
- `migrate_from_sqlite.py` — copies the existing rows from the `.db` files into Supabase.
- `requirements.txt` — Python deps for the migration script.
- `.env.example` — template for the DB connection string.

---

## 1. Create the Supabase project

1. Sign in at <https://supabase.com> → **New project**.
2. Pick a name, a strong **database password** (save it), and a region close to site.
3. Wait for it to finish provisioning (~2 min).

## 2. Create the schema

1. Supabase Dashboard → **SQL Editor** → **New query**.
2. Paste the entire contents of `schema.sql` → **Run**.
3. Check **Table Editor** — you should see `spools`, `bom`, `inventory`, etc. (all empty).

`schema.sql` is safe to re-run.

## 3. Load the existing data

```bash
# from the project root:  d:\my latest software\team piping - next final v2
python -m pip install -r supabase/requirements.txt

copy supabase\.env.example supabase\.env        # Windows
#  then edit supabase\.env and paste your connection string
```

Get the connection string from **Project Settings → Database → Connection string → URI**
(use the **direct** connection, host `db.<ref>.supabase.co`, port `5432`). It looks like:

```
postgresql://postgres:YOUR-PASSWORD@db.abcdefgh.supabase.co:5432/postgres
```

Then run:

```bash
python supabase/migrate_from_sqlite.py --dry-run     # preview row counts, writes nothing
python supabase/migrate_from_sqlite.py --truncate    # actually load (clears target tables first)
```

Expected: ~8,971 `spools`, 56 `manpower_reports`, 10 `user_credentials`,
466 `user_log`, 466 `user_sessions`, 16 `bom`, 8 `inventory`.

Re-run any time with `--truncate` to reload from scratch, or
`--only spools` to redo one table.

## 4. Point a client at it

**Streamlit app** (verification scaffold): see `../streamlit_app/`.
Copy `streamlit_app/.streamlit/secrets.toml.example` → `secrets.toml`,
paste the **Session pooler** connection string (add the `+psycopg2`
prefix as shown), then:

```bash
python -m pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

Log in with a username/password from `user_credentials` (unchanged from
the desktop app).

**Existing Tkinter app**: it still uses local SQLite. To switch it over,
replace `sqlite3.connect(...)` in `utils.py` with a `psycopg2` connection
to the same `DATABASE_URL`; the SQL is close to portable (main change:
`DATE(col)` → `col::date`, `?` placeholders → `%s`).

---

## Security notes

- **RLS is on with no anon policies** → the public `anon` / `authenticated`
  API keys can't touch any table. Server-side code (the migration script,
  the Streamlit app) connects with the full Postgres credentials and
  bypasses RLS. Never put that connection string or the `service_role`
  key in browser-side code.
- `user_credentials` still holds **plaintext passwords** (1:1 with the old
  app). Recommended follow-ups: move auth to Supabase Auth, or hash with
  `pgcrypto` (`crypt(pw, gen_salt('bf'))`).
- Do **not** commit `supabase/.env` or `streamlit_app/.streamlit/secrets.toml`.
- Enable **Point-in-Time Recovery / daily backups** in the Supabase
  dashboard once real data is in.
