-- AI Model Compression Jobs Tracking
-- Version: 31.0

-- Main compression jobs table
CREATE TABLE IF NOT EXISTS public.ai_compression_jobs (
    job_id TEXT PRIMARY KEY,
    batch_id UUID,
    user_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    original_size_gb DECIMAL(8, 2) NOT NULL,
    compressed_size_gb DECIMAL(8, 2),
    compression_method TEXT NOT NULL CHECK (compression_method IN ('4bit_awq', '2bit_gguf', '8bit_fp8', 'structural_pruning')),
    job_status TEXT DEFAULT 'queued' CHECK (job_status IN ('queued', 'compressing', 'completed', 'failed', 'cancelled')),
    download_url TEXT,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bulk compression batches
CREATE TABLE IF NOT EXISTS public.bulk_compression_batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    total_models_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    batch_status TEXT DEFAULT 'processing' CHECK (batch_status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Model accuracy benchmarks
CREATE TABLE IF NOT EXISTS public.model_accuracy_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT REFERENCES public.ai_compression_jobs(job_id) ON DELETE CASCADE,
    test_dataset_token TEXT NOT NULL,
    teacher_accuracy_score DECIMAL(5, 2),
    student_accuracy_score DECIMAL(5, 2),
    perplexity_loss_delta DECIMAL(6, 4),
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_compression_jobs_user ON public.ai_compression_jobs(user_id);
CREATE INDEX idx_compression_jobs_status ON public.ai_compression_jobs(job_status);
CREATE INDEX idx_compression_jobs_created ON public.ai_compression_jobs(created_at);
CREATE INDEX idx_bulk_batches_user ON public.bulk_compression_batches(user_id);
CREATE INDEX idx_benchmarks_job ON public.model_accuracy_benchmarks(job_id);

-- RLS
ALTER TABLE public.ai_compression_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bulk_compression_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_accuracy_benchmarks ENABLE ROW LEVEL SECURITY;
