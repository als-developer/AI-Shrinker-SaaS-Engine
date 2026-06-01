-- Cache Invalidation and Management Tables
-- Version: 31.0

-- Cache invalidation events
CREATE TABLE IF NOT EXISTS public.cache_invalidation_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key_pattern TEXT NOT NULL,
    invalidation_reason TEXT,
    triggered_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cache statistics
CREATE TABLE IF NOT EXISTS public.cache_statistics (
    stat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_level TEXT NOT NULL,
    hits BIGINT DEFAULT 0,
    misses BIGINT DEFAULT 0,
    evictions BIGINT DEFAULT 0,
    memory_used_mb DECIMAL(10, 2),
    record_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cache_level, record_date)
);

-- Preload cache jobs
CREATE TABLE IF NOT EXISTS public.cache_preload_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name TEXT NOT NULL,
    cache_keys TEXT[],
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cache_invalidation_pattern ON public.cache_invalidation_events(cache_key_pattern);
CREATE INDEX idx_cache_invalidation_time ON public.cache_invalidation_events(created_at DESC);
CREATE INDEX idx_cache_stats_date ON public.cache_statistics(record_date);
CREATE INDEX idx_cache_preload_status ON public.cache_preload_jobs(status);

-- RLS
ALTER TABLE public.cache_invalidation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cache_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cache_preload_jobs ENABLE ROW LEVEL SECURITY;
