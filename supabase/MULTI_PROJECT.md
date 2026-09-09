# Running the app for more than one project

Model: **one Supabase database per project, each with its own
`user_credentials`.** Nothing is shared between projects — separate
database, separate users, separate backups.

You can serve them from **one website** (recommended) or from a separate
Streamlit deployment per project.

---

## One website, project picker at sign-in  (recommended)

The app already supports this. In `streamlit_app/.streamlit/secrets.toml`
(or the Streamlit Cloud **Secrets** box) add a `[projects]` table and one
`[connections.<name>]` block per Supabase database:

```toml
[projects]
"PM0045 - Prefchem UG" = "supabase"
"PM0100 - Next Job"     = "supabase_pm0100"

[connections.supabase]
url = "postgresql+psycopg2://postgres.<ref-A>:<pw-A>@aws-0-<region>.pooler.supabase.com:5432/postgres"

[connections.supabase_pm0100]
url = "postgresql+psycopg2://postgres.<ref-B>:<pw-B>@aws-0-<region>.pooler.supabase.com:5432/postgres"
```

The sign-in screen then shows a **Project** dropdown. After the user
picks one, the login is checked against **that project's**
`user_credentials`, and every query, import, snapshot and setting for the
session runs on that database. Signing out (or the 30-min idle timeout)
clears the choice and the cache, so the next person picks again.

Still create each project's Supabase database and seed its admin exactly
as below — only the deployment step changes (one app instead of many).

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

### 2. Wire it into the website
**One website:** open your existing Streamlit Cloud app → **⋮ → Settings →
Secrets** → add the new `[connections.<name>]` block and a `[projects]`
line for it (see the top of this file). Save; the app reboots and the new
project appears in the sign-in dropdown.

**Separate deployment instead:** share.streamlit.io → **Create app** →
repo `muhamadsahma7-cloud/team-piping`, branch `main`, main file
`streamlit_app/app.py`, Python 3.12 → Secrets = just
`[connections.supabase] url = "…new project…"` → Deploy → restrict Sharing
to that team.

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

