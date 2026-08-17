-- Schema for blogger-agent-tfg posts
-- Target project: stqtpbdzqgcbaqdvrsij (supabase-secret MUST resolve to this project)
-- Apply command (pick one):
--   a) Supabase Dashboard → SQL Editor → paste this file → Run
--   b) supabase db push --linked (after `supabase link --project-ref stqtpbdzqgcbaqdvrsij`)
-- The "Public read" SELECT policy (REQ-3) grants anon read access; if it is
-- missing, the frontend sees zero posts with no error.

CREATE TABLE IF NOT EXISTS posts (
  id            text PRIMARY KEY,
  job_id        text,
  slug          text UNIQUE NOT NULL,
  title         text NOT NULL,
  description   text,
  content       text NOT NULL,
  author        text NOT NULL DEFAULT 'Blogger Agent',
  date          date NOT NULL,
  word_count    integer,
  reading_time  integer,
  keywords      text[],
  tags          text[],
  cover_image_url text,
  style_source      text,
  style_source_url  text,
  status            text,
  error_message     text,
  created_at    timestamptz DEFAULT now()
);

-- Migration note (existing databases; fresh installs get CREATE TABLE above):
--   ALTER TABLE posts ADD COLUMN style_source text;
--   ALTER TABLE posts ADD COLUMN style_source_url text;
--   ALTER TABLE posts ADD COLUMN job_id text;
--   ALTER TABLE posts ADD COLUMN status text;
--   ALTER TABLE posts ADD COLUMN error_message text;

-- Public read policy (TFG demo — no auth)
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON posts
  FOR SELECT USING (true);

CREATE POLICY "Service role write" ON posts
  FOR ALL USING (auth.role() = 'service_role');
