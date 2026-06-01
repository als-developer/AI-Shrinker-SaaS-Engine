-- System Telemetry and Monitoring Tables
-- Version: 31.0

-- Node telemetry data
CREATE TABLE IF NOT EXISTS public.node_telemetry (
    telemetry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id TEXT NOT NULL,
    region TEXT NOT NULL,
    cpu_percent DECIMAL(5, 2),
    memory_used_mb DECIMAL(10, 2),
    memory_total_mb DECIMAL(10, 2),
    disk_used_gb DECIMAL(10, 2),
    disk_total_gb DECIMAL(10, 2),
    requests_per_second INTEGER,
    avg_latency_ms DECIMAL(8, 2),
    error_rate DECIMAL(6, 4),
    active_connections INTEGER,
    status TEXT DEFAULT 'healthy',
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API endpoint metrics
CREATE TABLE IF NOT EXISTS public.api_endpoint_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    total_latency_ms DECIMAL(15, 2) DEFAULT 0,
    avg_latency_ms DECIMAL(8, 2),
    p50_latency_ms DECIMAL(8, 2),
    p90_latency_ms DECIMAL(8, 2),
    p99_latency_ms DECIMAL(8, 2),
    hour_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily summary metrics
CREATE TABLE IF NOT EXISTS public.daily_metrics_summary (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_api_calls INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    total_revenue_usd DECIMAL(12, 2) DEFAULT 0,
    total_compression_jobs INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(8, 2),
    uptime_percentage DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- Indexes
CREATE INDEX idx_node_telemetry_node ON public.node_telemetry(node_id, collected_at);
CREATE INDEX idx_node_telemetry_time ON public.node_telemetry(collected_at DESC);
CREATE INDEX idx_api_metrics_endpoint ON public.api_endpoint_metrics(endpoint, hour_bucket);
CREATE INDEX idx_api_metrics_time ON public.api_endpoint_metrics(hour_bucket DESC);
CREATE INDEX idx_daily_metrics_date ON public.daily_metrics_summary(date DESC);

-- RLS
ALTER TABLE public.node_telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_endpoint_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_metrics_summary ENABLE ROW LEVEL SECURITY;
