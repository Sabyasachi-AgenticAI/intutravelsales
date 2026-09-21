-- Owner Control tab v1: coupon editing + active-hours scheduling.
-- Run this in the Supabase SQL Editor for the cpoxlwfvgtifgybjyvnm project
-- (the same project offers/demo_calls/demo_bookings already live in).

-- 1. Let the existing publishable key UPDATE and INSERT offers (it was
-- select-only before this — offers.py never wrote to this table, so an
-- insert policy was never added).
drop policy if exists "offers_update_public" on public.offers;
create policy "offers_update_public"
  on public.offers
  for update
  using (true)
  with check (true);

drop policy if exists "offers_insert_public" on public.offers;
create policy "offers_insert_public"
  on public.offers
  for insert
  with check (true);

drop policy if exists "offers_delete_public" on public.offers;
create policy "offers_delete_public"
  on public.offers
  for delete
  using (true);

-- 2. Weekly active-hours schedule (one row per day, Sun=0..Sat=6).
create table if not exists public.store_hours (
  id serial primary key,
  day_of_week smallint not null check (day_of_week between 0 and 6),
  open_time time,
  close_time time,
  closed boolean not null default false,
  constraint store_hours_day_unique unique (day_of_week)
);

alter table public.store_hours enable row level security;
drop policy if exists "store_hours_select_public" on public.store_hours;
drop policy if exists "store_hours_update_public" on public.store_hours;
drop policy if exists "store_hours_insert_public" on public.store_hours;
create policy "store_hours_select_public" on public.store_hours for select using (true);
create policy "store_hours_update_public" on public.store_hours for update using (true) with check (true);
create policy "store_hours_insert_public" on public.store_hours for insert with check (true);

insert into public.store_hours (day_of_week, open_time, close_time, closed) values
  (1, '08:00', '18:00', false),
  (2, '08:00', '18:00', false),
  (3, '08:00', '18:00', false),
  (4, '08:00', '18:00', false),
  (5, '08:00', '18:00', false),
  (6, '09:00', '14:00', false),
  (0, null, null, true)
on conflict (day_of_week) do nothing;

-- 3. Singleton settings row for the manual AI on/off override.
create table if not exists public.store_settings (
  id boolean primary key default true check (id),
  ai_override text not null default 'auto' check (ai_override in ('auto', 'on', 'off'))
);

alter table public.store_settings enable row level security;
drop policy if exists "store_settings_select_public" on public.store_settings;
drop policy if exists "store_settings_update_public" on public.store_settings;
drop policy if exists "store_settings_insert_public" on public.store_settings;
create policy "store_settings_select_public" on public.store_settings for select using (true);
create policy "store_settings_update_public" on public.store_settings for update using (true) with check (true);
create policy "store_settings_insert_public" on public.store_settings for insert with check (true);

insert into public.store_settings (id, ai_override) values (true, 'auto')
on conflict (id) do nothing;
