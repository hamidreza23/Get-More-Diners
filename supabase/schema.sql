-- RESTAURANT SAAS DATABASE SCHEMA
-- This schema supports multi-tenant restaurant management with campaign functionality
-- USERS come from Supabase Auth; we reference auth.users by uid

-- Enable required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pg_trgm";
create extension if not exists "btree_gin";

-- RESTAURANTS
-- Each restaurant is owned by a user from Supabase Auth
create table public.restaurants (
  id uuid primary key default uuid_generate_v4(),
  owner_user_id uuid not null, -- auth.users.id
  name text not null,
  cuisine text,
  city text,
  state text,
  contact_email text,
  contact_phone text,
  website_url text,
  created_at timestamptz default now(),
  constraint fk_owner foreign key (owner_user_id) references auth.users (id) on delete cascade
);

-- Ensure one restaurant per owner (required by app upsert logic)
alter table public.restaurants
  add constraint uq_restaurants_owner unique (owner_user_id);

-- DINERS
-- Customer database for marketing campaigns
create table public.diners (
  id uuid primary key default uuid_generate_v4(),
  first_name text,
  last_name text,
  seniority text, -- 'director','vp','head','c_suite', or raw
  city text,
  state text,
  address_text text,
  interests text[], -- e.g. ['fine_dining','pubs','coffee_shops']
  email text unique,
  phone text unique,
  consent_email boolean default true,
  consent_sms boolean default true
);

-- Indexes for efficient diner queries
create index diners_city_idx on public.diners (city);
create index diners_state_idx on public.diners (state);
create index diners_interests_gin on public.diners using gin (interests);
create index diners_trgm_city on public.diners using gin (city gin_trgm_ops);

-- CAMPAIGNS
-- Marketing campaigns created by restaurant owners
create table public.campaigns (
  id uuid primary key default uuid_generate_v4(),
  restaurant_id uuid not null references public.restaurants(id) on delete cascade,
  channel text not null check (channel in ('email','sms')),
  subject text,
  body text not null,
  audience_filter_json jsonb,
  created_at timestamptz default now()
);

-- CAMPAIGN RECIPIENTS
-- Track who received each campaign and delivery status
create table public.campaign_recipients (
  id uuid primary key default uuid_generate_v4(),
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  diner_id uuid not null references public.diners(id),
  delivery_status text not null check (delivery_status in ('simulated_sent','simulated_failed')),
  preview_payload_json jsonb
);

-- ROW LEVEL SECURITY (RLS)
-- Enable RLS on all tenant-specific tables
alter table public.restaurants enable row level security;
alter table public.campaigns enable row level security;
alter table public.campaign_recipients enable row level security;

-- RESTAURANT POLICIES
-- Restaurant owners can read their own restaurants
create policy "restaurant_owner_read"
on public.restaurants for select
using (owner_user_id = auth.uid());

-- Restaurant owners can perform all operations on their restaurants
create policy "restaurant_owner_write"
on public.restaurants for all
using (owner_user_id = auth.uid())
with check (owner_user_id = auth.uid());

-- CAMPAIGN POLICIES
-- Campaigns are visible only to restaurant owners
create policy "campaigns_by_owner"
on public.campaigns for select
using (exists (
  select 1 from public.restaurants r
  where r.id = campaigns.restaurant_id and r.owner_user_id = auth.uid()
));

-- Only restaurant owners can create campaigns for their restaurants
create policy "campaigns_insert_owner"
on public.campaigns for insert
with check (exists (
  select 1 from public.restaurants r
  where r.id = restaurant_id and r.owner_user_id = auth.uid()
));

-- CAMPAIGN RECIPIENTS POLICIES
-- Recipients are visible via campaign → restaurant ownership chain
create policy "recips_by_owner"
on public.campaign_recipients for select
using (exists (
  select 1 from public.campaigns c
  join public.restaurants r on r.id = c.restaurant_id
  where c.id = campaign_recipients.campaign_id and r.owner_user_id = auth.uid()
));

-- Only restaurant owners can add recipients to their campaigns
create policy "recips_insert_owner"
on public.campaign_recipients for insert
with check (exists (
  select 1 from public.campaigns c
  join public.restaurants r on r.id = c.restaurant_id
  where c.id = campaign_id and r.owner_user_id = auth.uid()
));
