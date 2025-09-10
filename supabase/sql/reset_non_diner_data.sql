-- Clean project data while preserving diners
-- Run this in Supabase SQL editor or psql as a privileged user

begin;

-- Optional: log what will be deleted
-- select count(*) as recip_count from public.campaign_recipients;
-- select count(*) as campaign_count from public.campaigns;
-- select count(*) as restaurant_count from public.restaurants;
-- select count(*) as deleted_users_count from public.deleted_users;

-- Truncate tables in dependency order to avoid FK issues
truncate table public.campaign_recipients;
truncate table public.campaigns;
truncate table public.restaurants;

-- Optional auxiliary table used by delete-account route
do $$ begin
  if exists (select 1 from information_schema.tables where table_schema='public' and table_name='deleted_users') then
    truncate table public.deleted_users;
  end if;
end $$;

-- Re-assert one-restaurant-per-owner invariant
do $$ begin
  alter table public.restaurants add constraint uq_restaurants_owner unique (owner_user_id);
exception when duplicate_object then
  null;
end $$;

commit;

-- Verify
-- select count(*) as recip_count from public.campaign_recipients;
-- select count(*) as campaign_count from public.campaigns;
-- select count(*) as restaurant_count from public.restaurants;
