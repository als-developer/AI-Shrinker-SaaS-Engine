-- API Key Management Tables
-- Version: 31.0

-- Developer API keys (hashed storage)
CREATE TABLE IF NOT EXISTS public.developer_api_keys (
    key_hash TEXT PRIMARY KEY,  -- SHA-256 hash of the raw key
    developer_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    key_prefix TEXT,  -- First 8 chars for identification
    permissions JSONB DEFAULT '["read", "write"]'::JSONB,
    allowed_ips TEXT[] DEFAULT '{}',
    rate_limit_profile TEXT DEFAULT 'developer_tier',
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason TEXT
);

-- API key usage logs
CREATE TABLE IF NOT EXISTS public.api_key_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT REFERENCES public.developer_api_keys(key_hash) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rate limit violations
CREATE TABLE IF NOT EXISTS public.rate_limit_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT REFERENCES public.developer_api_keys(key_hash) ON DELETE CASCADE,
    ip_address INET,
    limit_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_api_keys_developer ON public.developer_api_keys(developer_id);
CREATE INDEX idx_api_keys_active ON public.developer_api_keys(is_active);
CREATE INDEX idx_api_usage_key_hash ON public.api_key_usage(key_hash);
CREATE INDEX idx_api_usage_created ON public.api_key_usage(created_at);
CREATE INDEX idx_rate_limit_key ON public.rate_limit_violations(key_hash);

-- RLS
ALTER TABLE public.developer_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_key_usage ENABLE ROW LEVEL SECURITY;

-- Function to hash API key
CREATE OR REPLACE FUNCTION hash_api_key(raw_key TEXT)
RETURNS TEXT AS $$
    SELECT encode(sha256(raw_key::bytea), 'hex');
$$ LANGUAGE sql IMMUTABLE;
