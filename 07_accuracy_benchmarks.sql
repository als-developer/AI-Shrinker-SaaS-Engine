-- Extended Accuracy and Performance Benchmarks
-- Version: 31.0

-- Benchmark test datasets
CREATE TABLE IF NOT EXISTS public.benchmark_datasets (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name TEXT UNIQUE NOT NULL,
    dataset_type TEXT CHECK (dataset_type IN ('mmlu', 'gsm8k', 'hellaswag', 'truthfulqa', 'custom')),
    total_questions INTEGER,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Benchmark results per model
CREATE TABLE IF NOT EXISTS public.model_benchmark_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT REFERENCES public.ai_compression_jobs(job_id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES public.benchmark_datasets(dataset_id),
    accuracy_score DECIMAL(5, 2),
    precision_score DECIMAL(5, 2),
    recall_score DECIMAL(5, 2),
    f1_score DECIMAL(5, 2),
    latency_ms INTEGER,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default benchmark datasets
INSERT INTO public.benchmark_datasets (dataset_name, dataset_type, total_questions) VALUES
    ('MMLU (Massive Multitask Language Understanding)', 'mmlu', 14000),
    ('GSM8K (Grade School Math)', 'gsm8k', 1319),
    ('HellaSwag (Common Sense Reasoning)', 'hellaswag', 10042),
    ('TruthfulQA (Truthfulness Assessment)', 'truthfulqa', 817);

-- Indexes
CREATE INDEX idx_benchmark_results_job ON public.model_benchmark_results(job_id);
CREATE INDEX idx_benchmark_results_dataset ON public.model_benchmark_results(dataset_id);

-- RLS
ALTER TABLE public.benchmark_datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_benchmark_results ENABLE ROW LEVEL SECURITY;
