# Putting the app online (Streamlit Community Cloud — free)

The app already talks to Supabase over the internet, so "going online" just
means hosting the Streamlit front-end somewhere other than your laptop.

## 1. Put the code on GitHub

From the project root (`d:\my latest software\team piping - next final v2`):

```bash
git init
git add .
git commit -m "Team Piping - Streamlit + Supabase"
git branch -M main
git remote add origin https://github.com/<you>/team-piping.git
git push -u origin main
```

`.gitignore` already excludes the secrets, the local `.db` files and scratch
output. **Confirm** `streamlit_app/.streamlit/secrets.toml` and `supabase/.env`
are NOT in the push (`git status` before committing).

## 2. Create the app

1. Go to <https://share.streamlit.io> → sign in with GitHub → **New app**.
2. Repository: your repo · Branch: `main`
3. **Main file path:** `streamlit_app/app.py`
4. **Advanced settings → Python version:** 3.11 or 3.12
5. Deploy.

Streamlit Cloud installs from `streamlit_app/requirements.txt` automatically
(same folder as the main file).

## 3. Add the database secret

App → **⋮ → Settings → Secrets**, paste (the Session-pooler string, same as
your local `streamlit_app/.streamlit/secrets.toml`):

```toml
[connections.supabase]
url = "postgresql+psycopg2://postgres.tsatsrprwaebbmiojslh:<PASSWORD>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
```

Use the **Session pooler** host (IPv4). Save → the app reboots.

## 4. Lock it down

- App → Settings → **Sharing**: set to *"Only specific people can view this app"*
  and add your team's emails (otherwise the URL is public — anyone still hits the
  login screen, but keep it restricted).
- The `user_credentials` table still holds **plaintext passwords**. Before wider
  rollout, move to hashed passwords (pgcrypto `crypt()`), or Supabase Auth.
- In Supabase → **Database → Backups**, confirm daily backups are on.

## Updating later

`git push` to `main` → Streamlit Cloud redeploys automatically.

---

## Alternatives

| Host | Notes |
|---|---|
| Render / Railway | `pip install -r streamlit_app/requirements.txt` then `streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0`. Set the secret as env or a mounted `secrets.toml`. |
| Company VPS | `streamlit run` behind nginx + TLS; run under systemd. |
| Hugging Face Spaces | Streamlit SDK space; put secrets in Space settings. |
