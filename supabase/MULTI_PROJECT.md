# Running the app for more than one project

Model: **one Supabase database per project, its own `user_credentials`.**
Same GitHub repo, one Streamlit Cloud app per project. No code changes.

Nothing is shared between projects — separate database, separate users,
separate URL, separate backups.

---

## Stand up a new project (≈15 min)

### 1. New Supabase database
1. supabase.com → **New project**. Name it for the project (e.g.
   `team-piping-<code>`). Save the **database password**.
2. **SQL Editor** → paste all of `supabase/schema.sql` → **Run**
   (creates every table empty, RLS on).
3. Still in SQL Editor, seed the first admin (safe to re-run — updates the
   password if `admin` already exists):
   ```sql
   insert into public.user_credentials (username, password, permission)
   values ('admin', 'a-strong-password', 'all')
   on conflict (username) do update
     set password = excluded.password, permission = excluded.permission;
   ```
4. **Connect** button → **Session pooler** → copy the URI. It looks like
   `postgresql://postgres.<ref>:<PW>@aws-0-<region>.pooler.supabase.com:5432/postgres`.
   Percent-encode any special characters in the password (`@` → `%40`, …).

### 2. New Streamlit Cloud app (same repo)
1. share.streamlit.io → **Create app** → repo
   `muhamadsahma7-cloud/team-piping`, branch `main`,
   **Main file `streamlit_app/app.py`**, Python 3.12.
2. **Advanced → Secrets**:
   ```toml
   [connections.supabase]
   url = "postgresql+psycopg2://postgres.<ref>:<PW-encoded>@aws-0-<region>.pooler.supabase.com:5432/postgres"
   ```
   (add the `+psycopg2` prefix)
3. **Deploy** → you get a second URL (e.g. `team-piping-<code>.streamlit.app`).
4. App menu **⋮ → Settings → Sharing** → limit to that project's team emails.

### 3. Load the project's data
Sign in as `admin` on the new URL, then:
- **Data admin → Import spools from Excel** — master-format `.xlsx` for the
  new project (replaces `spools`).
- **Users & access** — add the rest of that project's users.
- **Targets & plan** — set plan start / target / rest days / holidays.
- **Manpower** — start logging daily fitter/welder counts.
- `bom` / `inventory`: no in-app importer yet — load with
  `supabase/migrate_from_sqlite.py --only bom` style, or `INSERT`s in the
  SQL Editor, if that project uses them.

---

## Keeping projects in sync

- **Code**: every `git push` to `main` redeploys **all** the apps — one
  codebase, many databases.
- **Schema changes** (a new column, etc.): run the same `ALTER TABLE …`
  in **each project's** Supabase SQL Editor. Keep `supabase/schema.sql`
  as the master so a brand-new project always starts current.
- **Backups**: each Supabase project has its own daily backups
  (Dashboard → Database → Backups) and its own in-app `backup_spools_*`
  snapshots.

---

## If you'd rather have one URL

A single app can pick the project at login instead:
- Put one block per project in `secrets.toml`
  (`[connections.pm0045]`, `[connections.pm0100]`, …).
- Add a **Project** dropdown on the sign-in screen; store the choice in
  `st.session_state`.
- `db.py` uses `st.connection(f"…{chosen}")` for every call; login then
  validates against that project's `user_credentials`.

~30 lines. Ask and it can be added — but a deployment per project is
simpler to run and keeps the isolation absolute.
