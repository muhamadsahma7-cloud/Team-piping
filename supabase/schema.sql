-- =====================================================================
--  Team Piping - Supabase (PostgreSQL) schema
--  Online replacement for the local SQLite files:
--    database/spool_tracking.db   -> spools, manpower_reports,
--                                    user_credentials, user_log, user_sessions
--    database/material_tracking.db -> bom, inventory
--
--  How to apply:
--    Supabase Dashboard -> SQL Editor -> paste this whole file -> Run.
--  Safe to re-run: every object uses CREATE ... IF NOT EXISTS / OR REPLACE.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Helper: keep an updated_at column fresh on UPDATE
-- ---------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =====================================================================
-- spools  (main tracking table)
-- All business columns kept as text to match the current data exactly
-- (e.g. wo_no is stored like '1.0', dates in mixed formats). Only
-- joint_size is numeric. A surrogate id is added so rows can be edited
-- online unambiguously.
-- =====================================================================
create table if not exists public.spools (
    id                       bigint generated always as identity primary key,
    wo_no                    text,
    zone                     text,               -- added later in the SQLite app
    status                   text,               -- issued | os | hold
    batch_no                 text,
    area                     text,
    location                 text,
    service                  text,
    iso_dwg_no               text,
    iso_run_no               text,
    rev                      text,
    test_pack_no             text,
    system_no                text,
    subsystem_no             text,
    test_pressure            text,
    line_no                  text,
    line_spec                text,
    dwg_spool_no             text,
    material_group           text,
    shop_field               text,               -- S (shop) | F (field)
    joint_no                 text,
    joint_size               numeric,
    schedule                 text,
    wps_no                   text,
    welding_process          text,
    welding_type             text,
    fitup_inspection_date    text,
    item_1                   text,
    sch_rating_1             text,
    heat_no_1                text,
    item_2                   text,
    sch_rating_2             text,
    heat_no_2                text,
    fu_report_no             text,
    welding_inspection_date  text,
    root_welder_no           text,
    capping_welder_no        text,
    welder_no                text,               -- welder's stencil/Welder No. (QR scan)
    visual_report_no         text,
    rt_bsr_date              text,
    rt_bsr_report_no         text,
    bsr_fresh_joint_status   text,
    total_film               text,
    film_acc                 text,
    film_rej                 text,
    length_rej               text,
    bsr_repair_one_status    text,
    bsr_repair_two_status    text,
    pwht_date                text,
    pwht_report_no           text,
    rt_asr_date              text,
    rt_asr_report_no         text,
    rt_asr_result            text,
    mpi_pt_date              text,
    mpi_pt_type              text,
    mpi_pt_report_no         text,
    mpi_pt_result            text,
    hardness_date            text,
    hardness_report_no       text,
    hardness_result          text,
    pmi_date                 text,
    pmi_report_no            text,
    pmi_result               text,
    ferrite_date             text,
    ferrite_report_no        text,
    painting_date            text,
    painting_report_no       text,
    irn_date                 text,
    irn_report_no            text,
    paint_system             text,
    paint_status             text,               -- Yes | No  (needs painting?)
    pwht                     text,
    fitup_date               text,
    welding_date             text,
    fitup_by                 text,               -- fitter name (QR scan)
    welding_by               text,               -- welder name (QR scan)
    delivery_order_no        text,
    delivery_date            text,
    site_do_no               text,
    site_delivery_date       text,
    remark                   text,
    workable                 text default '',
    created_at               timestamptz not null default now(),
    updated_at               timestamptz not null default now()
);

drop trigger if exists trg_spools_updated_at on public.spools;
create trigger trg_spools_updated_at
    before update on public.spools
    for each row execute function public.set_updated_at();

create index if not exists idx_spools_wo_no         on public.spools (wo_no);
create index if not exists idx_spools_iso_dwg_no    on public.spools (iso_dwg_no);
create index if not exists idx_spools_dwg_spool_no  on public.spools (dwg_spool_no);
create index if not exists idx_spools_test_pack_no  on public.spools (test_pack_no);
create index if not exists idx_spools_system_no     on public.spools (system_no);
create index if not exists idx_spools_subsystem_no  on public.spools (subsystem_no);
create index if not exists idx_spools_area          on public.spools (area);
create index if not exists idx_spools_zone          on public.spools (zone);
create index if not exists idx_spools_shop_field    on public.spools (shop_field);
create index if not exists idx_spools_status        on public.spools (status);
create index if not exists idx_spools_batch_no      on public.spools (batch_no);
create index if not exists idx_spools_line_no       on public.spools (line_no);
create index if not exists idx_spools_fitup_date    on public.spools (fitup_date);
create index if not exists idx_spools_welding_date  on public.spools (welding_date);
create index if not exists idx_spools_painting_date on public.spools (painting_date);
create index if not exists idx_spools_delivery_date on public.spools (delivery_date);
create index if not exists idx_spools_irn_date      on public.spools (irn_date);

-- =====================================================================
-- manpower_reports
-- =====================================================================
create table if not exists public.manpower_reports (
    id             bigint generated always as identity primary key,
    date           text unique,        -- 'YYYY-MM-DD'
    total_welders  integer,
    total_fitters  integer,
    created_at     timestamptz not null default now()
);

-- =====================================================================
-- bom  (bill of materials, from material_tracking.db)
-- =====================================================================
create table if not exists public.bom (
    id                  bigint generated always as identity primary key,
    iso_drawing_number  text,
    status              text,
    material_grade      text,
    part_name           text,
    item_code           text,
    description         text,
    size                text,
    sch_rating          text,
    quantity            numeric,
    created_at          timestamptz not null default now()
);
create index if not exists idx_bom_item_code   on public.bom (item_code);
create index if not exists idx_bom_iso_drawing on public.bom (iso_drawing_number);
create index if not exists idx_bom_status      on public.bom (status);

-- =====================================================================
-- inventory  (stock on hand, from material_tracking.db)
-- =====================================================================
create table if not exists public.inventory (
    id              bigint generated always as identity primary key,
    material_grade  text,
    part_name       text,
    item_code       text,
    description     text,
    size            text,
    sch_rating      text,
    quantity        numeric,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);
create index if not exists idx_inventory_item_code on public.inventory (item_code);

drop trigger if exists trg_inventory_updated_at on public.inventory;
create trigger trg_inventory_updated_at
    before update on public.inventory
    for each row execute function public.set_updated_at();

-- =====================================================================
-- user_credentials
-- NOTE: the SQLite app stores plaintext passwords. Kept here for a
-- 1:1 migration so the current app keeps working. Recommended next
-- step: move auth to Supabase Auth, or at least store password hashes
-- (pgcrypto: crypt(pw, gen_salt('bf'))). The `permission` column is a
-- comma-separated list of tab names, or the literal 'all'.
-- =====================================================================
create table if not exists public.user_credentials (
    username    text primary key,
    password    text not null,
    permission  text not null,
    created_at  timestamptz not null default now()
);

-- =====================================================================
-- user_log  (append-only login history)
-- =====================================================================
create table if not exists public.user_log (
    id          bigint generated always as identity primary key,
    username    text,
    login_time  timestamptz not null default now()
);
create index if not exists idx_user_log_username on public.user_log (username);

-- =====================================================================
-- user_sessions
-- =====================================================================
create table if not exists public.user_sessions (
    id          bigint generated always as identity primary key,
    username    text,
    login_time  text,
    active      integer default 1
);
create index if not exists idx_user_sessions_username on public.user_sessions (username);

-- =====================================================================
-- project_settings  (key/value: plan_start, target_date, scope, rest days)
-- =====================================================================
create table if not exists public.project_settings (
    key         text primary key,
    value       text,
    updated_at  timestamptz not null default now()
);

-- =====================================================================
-- qc_wcs_docs  (QC "WCS" document store — files held as bytea)
-- =====================================================================
create table if not exists public.qc_wcs_docs (
    id           bigint generated always as identity primary key,
    filename     text not null,
    mime         text,
    size_bytes   bigint,
    data         bytea not null,
    note         text,
    uploaded_by  text,
    uploaded_at  timestamptz not null default now()
);
create index if not exists idx_qc_wcs_uploaded_at on public.qc_wcs_docs (uploaded_at desc);

-- =====================================================================
-- QR scan progress update  (see supabase/qr_feature.sql for notes)
--   spools.qr_id   - one code per SPOOL, shared by all its joint rows;
--                    printed as the QR label
--   field_workers  - self-registered fitters / welders (name + PIN)
--   field_updates  - append-only audit; UNIQUE(spool_id, activity)
--                    blocks double entry at the database level (per joint)
-- =====================================================================
alter table public.spools add column if not exists qr_id text;
alter table public.spools add column if not exists fitup_by text;    -- fitter name
alter table public.spools add column if not exists welding_by text;  -- welder name
alter table public.spools add column if not exists welder_no text;   -- welder's stencil no
drop index if exists public.uq_spools_qr_id;
create index if not exists idx_spools_qr_id on public.spools (qr_id);

create table if not exists public.field_workers (
    id            bigint generated always as identity primary key,
    name          text not null,
    trade         text not null check (trade in ('Fitter', 'Welder', 'Both')),
    stamp_no      text,
    phone         text,
    pin           text not null,
    active        boolean not null default true,
    registered_at timestamptz not null default now()
);
create unique index if not exists uq_field_workers_name_trade
    on public.field_workers (lower(name), trade);

create table if not exists public.field_updates (
    id           bigint generated always as identity primary key,
    spool_id     bigint not null,             -- soft link (Excel re-import TRUNCATEs spools)
    qr_id        text,                         -- spool code, stable across re-imports
    joint_no     text,
    activity     text not null check (activity in ('Fit-Up', 'Welding')),
    work_date    text not null,
    worker_id    bigint references public.field_workers (id),
    worker_name  text,
    stamp_no     text,
    source       text not null default 'qr',
    app_user     text,
    recorded_at  timestamptz not null default now()
);
alter table public.field_updates add column if not exists qr_id text;
alter table public.field_updates add column if not exists joint_no text;
drop index if exists public.uq_field_updates_joint_activity;
create unique index if not exists uq_field_updates_joint_activity
    on public.field_updates (qr_id, joint_no, activity) where qr_id is not null;
create index if not exists idx_field_updates_recorded_at
    on public.field_updates (recorded_at desc);
create index if not exists idx_field_updates_qr
    on public.field_updates (qr_id);

-- =====================================================================
-- Row Level Security
-- RLS is ON for every table and NO anon/authenticated policies are
-- created. That means the public `anon` and `authenticated` API keys
-- can read/write NOTHING. The Streamlit app connects server-side with
-- the `service_role` key (or the direct Postgres connection string),
-- which bypasses RLS. Keep the service_role key OUT of any browser code.
--
-- When you later add Supabase Auth, add explicit policies such as:
--   create policy "read spools" on public.spools
--     for select to authenticated using (true);
-- =====================================================================
alter table public.spools            enable row level security;
alter table public.manpower_reports  enable row level security;
alter table public.bom               enable row level security;
alter table public.inventory         enable row level security;
alter table public.user_credentials  enable row level security;
alter table public.user_log          enable row level security;
alter table public.user_sessions     enable row level security;
alter table public.project_settings  enable row level security;
alter table public.qc_wcs_docs        enable row level security;
alter table public.field_workers     enable row level security;
alter table public.field_updates     enable row level security;

-- =====================================================================
-- First admin (a fresh database has no users). Uncomment, set a real
-- password, run once, then manage everyone else from the app's
-- "Users & access" page. Passwords are plain text (matching the app).
-- =====================================================================
-- insert into public.user_credentials (username, password, permission)
-- values ('admin', 'CHANGE-ME', 'all')
-- on conflict (username) do nothing;

-- =====================================================================
-- done
-- =====================================================================
