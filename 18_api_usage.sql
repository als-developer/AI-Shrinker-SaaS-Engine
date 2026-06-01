-- API Usage Analytics and Statistics
-- Version: 31.0

-- API usage logs (partitioned by month)
CREATE TABLE IF NOT EXISTS public.api_usage_logs (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id),
    org_id UUID REFERENCES public.organizations(org_id),
    api_key_hash TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hourly API usage aggregates
CREATE TABLE IF NOT EXISTS public.api_usage_hourly (
    hour_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    org_id UUID REFERENCES public.organizations(org_id),
    endpoint TEXT,
    total_requests INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    total_latency_ms BIGINT DEFAULT 0,
    avg_latency_ms DECIMAL(10, 2),
    PRIMARY KEY (hour_bucket, org_id, endpoint)
);

-- Daily API usage aggregates
CREATE TABLE IF NOT EXISTS public.api_usage_daily (
    date DATE NOT NULL,
    org_id UUID REFERENCES public.organizations(org_id),
    total_requests INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    total_revenue_usd DECIMAL(12, 4) DEFAULT 0,
    compression_jobs INTEGER DEFAULT 0,
    fact_checks INTEGER DEFAULT 0,
    payments INTEGER DEFAULT 0,
    PRIMARY KEY (date, org_id)
);

-- Indexes
CREATE INDEX idx_api_usage_user ON public.api_usage_logs(user_id, created_at DESC);
CREATE INDEX idx_api_usage_org ON public.api_usage_logs(org_id, created_at DESC);
CREATE INDEX idx_api_usage_endpoint ON public.api_usage_logs(endpoint);
CREATE INDEX idx_api_usage_created ON public.api_usage_logs(created_at);
CREATE INDEX idx_api_usage_hourly ON public.api_usage_hourly(hour_bucket DESC);
CREATE INDEX idx_api_usage_daily ON public.api_usage_daily(date DESC);

-- RLS
ALTER TABLE public.api_usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage_hourly ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage_daily ENABLE ROW LEVEL SECURITY;

-- Function to aggregate hourly data
CREATE OR REPLACE FUNCTION aggregate_api_usage_hourly()
RETURNS void AS $$
BEGIN
    INSERT INTO public.api_usage_hourly (hour_bucket, org_id, endpoint, total_requests, total_errors, total_latency_ms)
    SELECT 
        DATE_TRUNC('hour', created_at) as hour_bucket,
        org_id,
        endpoint,
        COUNT(*) as total_requests,
        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as total_errors,
        SUM(response_time_ms) as total_latency_ms
    FROM public.api_usage_logs
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY hour_bucket, org_id, endpoint
    ON CONFLICT (hour_bucket, org_id, endpoint) 
    DO UPDATE SET 
        total_requests = api_usage_hourly.total_requests + EXCLUDED.total_requests,
        total_errors = api_usage_hourly.total_errors + EXCLUDED.total_errors,
        total_latency_ms = api_usage_hourly.total_latency_ms + EXCLUDED.total_latency_ms;
END;
$$ LANGUAGE plpgsql;
