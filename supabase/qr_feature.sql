-- =====================================================================
--  Team Piping - QR scan progress update  (draft, 2026-09-09)
--
--  Adds:
--    spools.qr_id          - one code per SPOOL (shared by all its joint
--                            rows): work order / batch / ISO dwg / line /
--                            page / dwg spool. Printed as the QR label.
--    field_workers         - self-registered fitters / welders (name + PIN)
--    field_updates         - append-only audit of every QR fit-up / welding
--                            scan; UNIQUE(qr_id, joint_no, activity) blocks
--                            double entry at the database level (per joint).
--
--  Apply:  Supabase Dashboard -> SQL Editor -> paste -> Run.  Safe to re-run.
-- =====================================================================

-- one code per spool, written onto every joint row of that spool. On a
-- scan the app lists the spool's joints and the worker ticks which ones.
alter table public.spools add column if not exists qr_id text;
drop index if exists public.uq_spools_qr_id;          -- was unique in the first draft
create index if not exists idx_spools_qr_id on public.spools (qr_id);

-- the fitter / welder name (and, for a welder, his stencil/Welder No.,
-- next to the existing capping_welder_no) gets written onto the spool
-- row too, next to the date, when progress is recorded from a scan
alter table public.spools add column if not exists fitup_by text;
alter table public.spools add column if not exists welding_by text;
alter table public.spools add column if not exists welder_no text;

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
--
-- spool_id is a soft link (no FK) on purpose: the Data-admin Excel
-- re-import does TRUNCATE public.spools RESTART IDENTITY, which a FK
-- would block and which renumbers ids anyway. qr_id is copied in as a
-- stable handle - the app re-links printed QR codes by natural key on
-- every re-import, so field_updates.qr_id keeps pointing at the joint.
-- ---------------------------------------------------------------------
create table if not exists public.field_updates (
    id           bigint generated always as identity primary key,
    spool_id     bigint not null,
    qr_id        text,
    joint_no     text,
    activity     text not null check (activity in ('Fit-Up', 'Welding')),
    work_date    text not null,               -- 'YYYY-MM-DD' also written to spools
    worker_id    bigint references public.field_workers (id),
    worker_name  text,
    stamp_no     text,
    source       text not null default 'qr',
    app_user     text,
    recorded_at  timestamptz not null default now()
);
alter table public.field_updates add column if not exists qr_id text;
alter table public.field_updates add column if not exists joint_no text;
-- one Fit-Up + one Welding per joint of a spool = the double-entry guard
drop index if exists public.uq_field_updates_joint_activity;
create unique index if not exists uq_field_updates_joint_activity
    on public.field_updates (qr_id, joint_no, activity) where qr_id is not null;
create index if not exists idx_field_updates_recorded_at
    on public.field_updates (recorded_at desc);
create index if not exists idx_field_updates_qr
    on public.field_updates (qr_id);

alter table public.field_workers enable row level security;
alter table public.field_updates enable row level security;

-- =====================================================================
-- done
-- =====================================================================
