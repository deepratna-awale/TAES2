-- TAES 2 Database Initialization Script
-- This script sets up the initial database configuration

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create the TAES2 user with appropriate permissions
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'taes2_db_user') THEN
        CREATE USER taes2_db_user WITH PASSWORD 'postgres_admin_pass';
    END IF;
END
$$;

-- Grant necessary permissions to taes2_db_user
GRANT ALL PRIVILEGES ON DATABASE taes2_db TO taes2_db_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO taes2_db_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taes2_db_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taes2_db_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO taes2_db_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO taes2_db_user;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log initialization
\echo 'TAES 2 database initialization completed';
\echo 'Database: taes2_db';
\echo 'Admin User: taes2_db_user';
\echo 'App User: taes2_db_user';
\echo 'Extensions installed: uuid-ossp, pg_trgm';
\echo 'Ready for TAES 2 application startup';
