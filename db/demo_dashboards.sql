-- Demo dashboard tables for the intuService ops & shop views.
--
-- These back the live feeds in frontend/public/ops.html and shop.html, and are
-- written to by the voice agent (my-agent/src/integrations/dashboard.py).
--
-- Run this once, in the Supabase SQL Editor for the target project
-- (https://cpoxlwfvgtifgybjyvnm.supabase.co). Safe to re-run: it is idempotent.
--
-- Security note: these tables are intentionally world-read/insert for a public
-- demo. The publishable (anon) key is the only key that should ever touch them
-- from client code — never embed the secret key.

-- ---------------------------------------------------------------- demo_calls
create table if not exists public.demo_calls (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),
  store        text not null,
  intent       text not null,
  summary      text not null,
  outcome      text not null,
  outcome_type text not null default 'good',   -- good | info | neutral | critical | upsell
  value        text,
  duration     text,
  upsell       text,
  extra        text
);

-- -------------------------------------------------------------- demo_bookings
create table if not exists public.demo_bookings (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  store       text not null default 'Aramingo',
  arrive_at   text,
  title       text not null,
  customer    text not null,
  vehicle     text not null,
  severity    text not null default 'routine',  -- routine | diag | urgent
  badges      text[] not null default '{}',
  note        text,
  complaint   text,
  triage      text,
  dtc         text,
  parts       jsonb not null default '[]',       -- array of [name, "in" | "ord"]
  promised    text,
  booked_via  text
);

-- ----------------------------------------------------------------------- RLS
alter table public.demo_calls    enable row level security;
alter table public.demo_bookings enable row level security;

-- Public read + insert (demo scratch tables). Dropped first so re-runs don't error.
drop policy if exists demo_calls_read      on public.demo_calls;
drop policy if exists demo_calls_insert    on public.demo_calls;
drop policy if exists demo_bookings_read   on public.demo_bookings;
drop policy if exists demo_bookings_insert on public.demo_bookings;

create policy demo_calls_read      on public.demo_calls    for select using (true);
create policy demo_calls_insert    on public.demo_calls    for insert with check (true);
create policy demo_bookings_read   on public.demo_bookings for select using (true);
create policy demo_bookings_insert on public.demo_bookings for insert with check (true);

-- ------------------------------------------------------------------ Realtime
-- The dashboards subscribe to INSERTs via postgres_changes, so both tables
-- must be in the supabase_realtime publication. Guarded so re-runs are no-ops.
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public' and tablename = 'demo_calls'
  ) then
    alter publication supabase_realtime add table public.demo_calls;
  end if;

  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public' and tablename = 'demo_bookings'
  ) then
    alter publication supabase_realtime add table public.demo_bookings;
  end if;
end $$;
