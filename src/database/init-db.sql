-- TAES 2 Database Initialization Script
-- Runs once, when the Postgres container creates its data directory.
-- The application role and database come from POSTGRES_USER / POSTGRES_DB.

SET timezone = 'UTC';

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
