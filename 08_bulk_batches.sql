-- Bulk Processing and Queue Management
-- Version: 31.0

-- Batch processing queue
CREATE TABLE IF NOT EXISTS public.processing_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_type TEXT CHECK (queue_type IN ('compression', 'payment', 'webhook', 'email', 'report')),
    payload JSONB NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Batch job history
CREATE TABLE IF NOT EXISTS public.batch_job_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID,
    job_type TEXT,
    total_items INTEGER,
    successful_items INTEGER,
    failed_items INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_queue_status ON public.processing_queue(status);
CREATE INDEX idx_queue_priority ON public.processing_queue(priority, created_at);
CREATE INDEX idx_batch_history_created ON public.batch_job_history(created_at);

-- RLS
ALTER TABLE public.processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batch_job_history ENABLE ROW LEVEL SECURITY;
