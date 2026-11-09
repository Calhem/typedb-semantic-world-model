-- PostgreSQL 18 smoke test for baseline B (Phase 1C). Throwaway schema, dropped at the end.
--   docker exec -i wm-postgres psql -U wm -d wm -v ON_ERROR_STOP=0 < environments/smoke/postgres_smoke.sql
\echo '== version'
SELECT version();
SHOW server_version;
CREATE SCHEMA smoke;
SET search_path = smoke;
CREATE EXTENSION IF NOT EXISTS btree_gist SCHEMA smoke;

\echo '== temporal primary key: one location per object at any valid time'
CREATE TABLE referent (id text, valid_at tstzrange NOT NULL,
  PRIMARY KEY (id, valid_at WITHOUT OVERLAPS));
CREATE TABLE located_at (obj text, place text, valid_at tstzrange NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (obj, valid_at WITHOUT OVERLAPS),
  FOREIGN KEY (obj, PERIOD valid_at) REFERENCES referent (id, PERIOD valid_at));
INSERT INTO referent VALUES ('box', '[2026-11-09 10:00Z,)');
INSERT INTO located_at (obj, place, valid_at) VALUES ('box', 'shelf-3', '[2026-11-09 10:03Z, 2026-11-09 10:06Z)');
INSERT INTO located_at (obj, place, valid_at) VALUES ('box', 'dock', '[2026-11-09 10:12Z,)');

\echo '== expected ERROR: overlapping valid time for the same object'
INSERT INTO located_at (obj, place, valid_at) VALUES ('box', 'bin', '[2026-11-09 10:05Z, 2026-11-09 10:08Z)');

\echo '== expected ERROR: temporal foreign key outside the referent''s lifetime'
INSERT INTO located_at (obj, place, valid_at) VALUES ('box', 'shelf-1', '[2026-11-09 09:00Z, 2026-11-09 09:30Z)');

\echo '== as-of query: where was the box at 10:04 and at 10:15?'
SELECT '10:04' AS t, place FROM located_at WHERE obj = 'box' AND valid_at @> '2026-11-09 10:04Z'::timestamptz
UNION ALL
SELECT '10:15', place FROM located_at WHERE obj = 'box' AND valid_at @> '2026-11-09 10:15Z'::timestamptz;

\echo '== cleanup'
RESET search_path;
DROP SCHEMA smoke CASCADE;
SELECT count(*) AS leftover_smoke_schemas FROM pg_namespace WHERE nspname = 'smoke';
