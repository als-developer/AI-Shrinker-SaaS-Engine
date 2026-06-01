-- Rate Limiting Configuration Tables
-- Version: 31.0

-- Rate limit profiles
CREATE TABLE IF NOT EXISTS public.rate_limit_profiles (
    profile_id TEXT PRIMARY KEY,
    requests_per_minute INTEGER NOT NULL,
    burst_capacity INTEGER NOT NULL,
    daily_limit INTEGER,
    monthly_limit INTEGER,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default profiles
INSERT INTO public.rate_limit_profiles (profile_id, requests_per_minute, burst_capacity, daily_limit, monthly_limit, description) VALUES
    ('free_tier', 10, 15, 100, 1000, 'Free tier rate limits'),
    ('developer_tier', 100, 150, 5000, 50000, 'Developer tier rate limits'),
    ('business_tier', 1000, 1500, 50000, 500000, 'Business tier rate limits'),
    ('enterprise_tier', 5000, 7500, 250000, 2500000, 'Enterprise tier rate limits')
ON CONFLICT (profile_id) DO NOTHING;

-- User rate limit overrides
CREATE TABLE IF NOT EXISTS public.rate_limit_overrides (
    override_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    custom_requests_per_minute INTEGER,
    custom_daily_limit INTEGER,
    valid_until TIMESTAMP WITH TIME ZONE,
    reason TEXT,
    created_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rate limit violation tracking
CREATE TABLE IF NOT EXISTS public.rate_limit_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id),
    api_key_hash TEXT,
    ip_address INET,
    endpoint TEXT,
    requests_per_minute INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rate_limit_user ON public.rate_limit_overrides(user_id);
CREATE INDEX idx_rate_limit_violations_user ON public.rate_limit_violations(user_id, created_at DESC);
CREATE INDEX idx_rate_limit_violations_ip ON public.rate_limit_violations(ip_address);

-- RLS
ALTER TABLE public.rate_limit_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rate_limit_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rate_limit_violations ENABLE ROW LEVEL SECURITY;
