-- Executed once, when the PostgreSQL data directory is first created.
-- Extensions must exist before Alembic creates the hypertables.

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Trigram index support for fast symbol / news title search.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Optional: semantic news clustering (docs/07-news-flow.md, ADR O5).
-- The image may not ship pgvector; failure here must not abort initialisation,
-- so it is attempted in a DO block.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgvector not available; news dedup will use in-memory vectors';
END
$$;
