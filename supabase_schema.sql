-- Supabase schema for the ACM TOMM subjective QoE study.
-- Paste this once into the Supabase SQL editor (Project -> SQL Editor -> New query).
--
-- It creates an append-only `responses` table: anonymous participants can INSERT
-- rows from the browser using the public anon key, but cannot read, update, or
-- delete anything. You (the project owner) read the data from the dashboard or
-- with export_responses.py using the service_role key.

create table if not exists public.responses (
    id              bigint generated always as identity primary key,
    created_at      timestamptz not null default now(),
    participant_id  text        not null,
    pair_id         text        not null,
    game            text,
    bandwidth_mbit  int,
    pair_index      int,
    video_a_kind    text,
    video_b_kind    text,
    video_a_file    text,
    video_b_file    text,
    score_a         int,
    score_b         int,
    which_real      text,
    is_correct      boolean,
    pairs_version   text,
    pairs_hash      text,
    user_agent      text,

    -- Reject malformed/junk inserts at the database. Because the publishable key
    -- is public, anyone can attempt an INSERT; these CHECKs ensure only
    -- well-formed rows are accepted. Legit submissions from the app always pass.
    constraint score_a_range    check (score_a between 1 and 5),
    constraint score_b_range    check (score_b between 1 and 5),
    constraint which_real_valid check (which_real in ('None','Both','Video A','Video B')),
    constraint game_valid       check (game in ('Forza','Fortnite','Kombat')),
    constraint bw_valid         check (bandwidth_mbit in (2,4,6,8,10))
);

-- If the table already exists without these constraints, add them with:
--   alter table public.responses
--     add constraint score_a_range    check (score_a between 1 and 5),
--     add constraint score_b_range    check (score_b between 1 and 5),
--     add constraint which_real_valid check (which_real in ('None','Both','Video A','Video B')),
--     add constraint game_valid       check (game in ('Forza','Fortnite','Kombat')),
--     add constraint bw_valid         check (bandwidth_mbit in (2,4,6,8,10));

-- Supabase has two access layers and BOTH are required:
--   1. GRANT  -> whether the anon role can reach the table via the Data/REST API
--   2. RLS    -> which rows that role may read/modify
-- A table created via SQL is not guaranteed to be reachable by anon unless the
-- privilege is granted, so we grant INSERT explicitly (reproducible regardless
-- of the project's Data API default-grant setting).
grant insert on table public.responses to anon;

-- Enable Row Level Security and allow ONLY inserts for the anonymous role.
alter table public.responses enable row level security;

drop policy if exists "anon insert responses" on public.responses;
create policy "anon insert responses"
    on public.responses
    for insert
    to anon
    with check (true);

-- No select/update/delete policy => participants cannot read or modify data.
-- (We deliberately do NOT grant select/update/delete to anon either.)

-- ---------------------------------------------------------------------------
-- API keys (current Supabase model):
--   * Browser/config.js -> PUBLISHABLE key (sb_publishable_...), maps to the
--     anon role. Legacy anon JWT keys also still work.
--   * export_responses.py -> SECRET key (sb_secret_...), bypasses RLS. Legacy
--     service_role JWT keys also still work. Keep it server-side only.
--
-- Verify after setup (run here as the owner -> you CAN read):
--   select count(*) from public.responses;
-- The anon insert path is verified by submitting a pair in the app or with the
-- curl commands in the README; anon reads return nothing by design.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Public aggregate view for the online stats dashboard (stats.html).
-- Exposes ONLY summary numbers per (game, bandwidth) -- never raw responses.
-- It runs as the view owner (security_invoker = false) so it can aggregate the
-- full table while anon, which has NO select on public.responses, can still
-- read these aggregates. Only the columns listed below are ever visible.
-- ---------------------------------------------------------------------------
create or replace view public.response_stats
    with (security_invoker = false) as
select
    game,
    bandwidth_mbit,
    count(*)::int as n,
    round(avg(case when video_a_kind = 'real'  then score_a else score_b end)::numeric, 3) as mean_mos_real,
    round(avg(case when video_a_kind = 'synth' then score_a else score_b end)::numeric, 3) as mean_mos_synth,
    round(avg(case when is_correct then 1 else 0 end)::numeric, 4) as detection_accuracy
from public.responses
group by game, bandwidth_mbit
order by bandwidth_mbit, game;

grant select on public.response_stats to anon;
