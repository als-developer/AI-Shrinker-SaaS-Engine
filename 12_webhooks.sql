-- Webhook Configuration and Delivery Tables
-- Version: 31.0

-- Webhook endpoints
CREATE TABLE IF NOT EXISTS public.webhook_endpoints (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id TEXT REFERENCES public.merchant_accounts(merchant_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    secret TEXT,
    events TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_limit INTEGER DEFAULT 100,
    timeout_ms INTEGER DEFAULT 5000,
    retry_count INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook delivery attempts
CREATE TABLE IF NOT EXISTS public.webhook_deliveries (
    delivery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID REFERENCES public.webhook_endpoints(webhook_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB,
    attempt_number INTEGER DEFAULT 1,
    status_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS public.webhook_statistics AS
SELECT 
    webhook_id,
    COUNT(*) as total_deliveries,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_deliveries,
    AVG(duration_ms) as avg_duration_ms,
    MAX(created_at) as last_delivery
FROM public.webhook_deliveries
GROUP BY webhook_id;

-- Indexes
CREATE INDEX idx_webhook_merchant ON public.webhook_endpoints(merchant_id);
CREATE INDEX idx_webhook_active ON public.webhook_endpoints(is_active);
CREATE INDEX idx_webhook_deliveries_webhook ON public.webhook_deliveries(webhook_id, created_at DESC);
CREATE INDEX idx_webhook_deliveries_created ON public.webhook_deliveries(created_at);

-- RLS
ALTER TABLE public.webhook_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.webhook_deliveries ENABLE ROW LEVEL SECURITY;
