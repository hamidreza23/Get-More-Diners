-- Reconcile restaurant schema with backend expectations
begin;

-- Ensure required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- Ensure required columns exist
alter table public.restaurants add column if not exists website_url text;
alter table public.restaurants add column if not exists logo_url text;
alter table public.restaurants add column if not exists caption text;

-- Ensure unique owner constraint exists
do $$ begin
  alter table public.restaurants add constraint uq_restaurants_owner unique (owner_user_id);
exception when duplicate_object then
  null;
end $$;

commit;
