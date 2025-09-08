-- Smart Home Database Initialization Script
-- This script initializes the PostgreSQL database for the Smart Home application

-- Create database (already created by docker-compose environment variables)
-- \c smarthome;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create schema for better organization (optional)
-- CREATE SCHEMA IF NOT EXISTS smarthome;
-- SET search_path TO smarthome, public;

-- The individual services will create their own tables via the application code
-- This is just for any global database setup if needed in the future

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE smarthome TO postgres;

-- Create indexes that might be useful across services
-- (Individual services will create their own specific indexes)

-- Log initialization
INSERT INTO pg_stat_statements_info(query) VALUES ('Smart Home Database Initialized') ON CONFLICT DO NOTHING;

-- Database initialization completed
SELECT 'Smart Home PostgreSQL Database Initialized Successfully' AS status;
