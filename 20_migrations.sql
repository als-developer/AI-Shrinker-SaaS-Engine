-- Database Schema Migration Tracking
-- Version: 31.0

-- Migrations table
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    migration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by TEXT,
    checksum TEXT,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- Current schema version tracking
CREATE TABLE IF NOT EXISTS public.schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_current BOOLEAN DEFAULT true
);

-- Insert initial migration record
INSERT INTO public.schema_version (version, applied_at, is_current) 
VALUES (31, NOW(), true) ON CONFLICT (version) DO NOTHING;

-- Function to record migrations
CREATE OR REPLACE FUNCTION record_migration(
    p_version INTEGER,
    p_name TEXT,
    p_duration_ms INTEGER,
    p_success BOOLEAN,
    p_error_message TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO public.schema_migrations (version, name, duration_ms, success, error_message, applied_by)
    VALUES (p_version, p_name, p_duration_ms, p_success, p_error_message, current_user);
    
    IF p_success THEN
        UPDATE public.schema_version SET is_current = false WHERE is_current = true;
        INSERT INTO public.schema_version (version) VALUES (p_version) ON CONFLICT (version) DO UPDATE SET is_current = true;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS
ALTER TABLE public.schema_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schema_version ENABLE ROW LEVEL SECURITY;
