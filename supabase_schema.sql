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
    user_agent      text
);

-- Enable Row Level Security and allow ONLY inserts for the anonymous role.
alter table public.responses enable row level security;

drop policy if exists "anon insert responses" on public.responses;
create policy "anon insert responses"
    on public.responses
    for insert
    to anon
    with check (true);

-- (No select/update/delete policy => participants cannot read or modify data.)
