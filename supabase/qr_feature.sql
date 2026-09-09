-- =====================================================================
--  Team Piping - QR scan progress update  (draft, 2026-09-09)
--
--  Adds:
--    spools.qr_id          - opaque per-joint code embedded in the QR label
--    field_workers         - self-registered fitters / welders (name + PIN)
--    field_updates         - append-only audit of every QR fit-up / welding
--                            scan; UNIQUE(spool_id, activity) blocks double
--                            entry at the database level.
--
--  Apply:  Supabase Dashboard -> SQL Editor -> paste -> Run.  Safe to re-run.
-- =====================================================================

-- opaque code per joint (row) - printed as the QR, stable across re-imports
alter table public.spools add column if not exists qr_id text;
create unique index if not exists uq_spools_qr_id
    on public.spools (qr_id) where qr_id is not null;

-- ---------------------------------------------------------------------
-- field_workers - a fitter / welder registers his own name once
-- ---------------------------------------------------------------------
create table if not exists public.field_workers (
    id            bigint generated always as identity primary key,
    name          text not null,
    trade         text not null check (trade in ('Fitter', 'Welder', 'Both')),
    stamp_no      text,                       -- welder stencil / fitter id
    phone         text,
    pin           text not null,              -- 4-6 digits, checked at scan time
    active        boolean not null default true,
    registered_at timestamptz not null default now()
);
create unique index if not exists uq_field_workers_name_trade
    on public.field_workers (lower(name), trade);

-- ---------------------------------------------------------------------
-- field_updates - one row per (joint, activity); the UNIQUE index is
-- what makes "cannot double entry" race-safe.
-- ---------------------------------------------------------------------
create table if not exists public.field_updates (
    id           bigint generated always as identity primary key,
    spool_id     bigint not null references public.spools (id),
    activity     text not null check (activity in ('Fit-Up', 'Welding')),
    work_date    text not null,               -- 'YYYY-MM-DD' also written to spools
    worker_id    bigint references public.field_workers (id),
    worker_name  text,
    stamp_no     text,
    source       text not null default 'qr',
    app_user     text,
    recorded_at  timestamptz not null default now()
);
create unique index if not exists uq_field_updates_joint_activity
    on public.field_updates (spool_id, activity);
create index if not exists idx_field_updates_recorded_at
    on public.field_updates (recorded_at desc);
create index if not exists idx_field_updates_spool
    on public.field_updates (spool_id);

alter table public.field_workers enable row level security;
alter table public.field_updates enable row level security;

-- =====================================================================
-- done
-- =====================================================================
