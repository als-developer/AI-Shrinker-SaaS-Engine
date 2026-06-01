-- Service Level Agreement (SLA) Tracking Tables
-- Version: 31.0

-- SLA contracts
CREATE TABLE IF NOT EXISTS public.sla_contracts (
    contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.organizations(org_id) ON DELETE CASCADE,
    sla_tier TEXT CHECK (sla_tier IN ('standard', 'premium', 'enterprise')),
    uptime_guarantee DECIMAL(5, 2) NOT NULL,
    max_latency_ms INTEGER NOT NULL,
    monthly_uptime_percentage DECIMAL(5, 2),
    refund_percentage DECIMAL(5, 2) DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SLA violation events
CREATE TABLE IF NOT EXISTS public.sla_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.organizations(org_id) ON DELETE CASCADE,
    contract_id UUID REFERENCES public.sla_contracts(contract_id),
    violation_type TEXT CHECK (violation_type IN ('uptime', 'latency', 'error_rate')),
    measured_value DECIMAL(10, 2),
    threshold_value DECIMAL(10, 2),
    violation_start TIMESTAMP WITH TIME ZONE,
    violation_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    refund_amount_usd DECIMAL(10, 2),
    refund_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SLA refunds
CREATE TABLE IF NOT EXISTS public.sla_refunds (
    refund_id TEXT PRIMARY KEY,
    org_id UUID REFERENCES public.organizations(org_id),
    violation_id UUID REFERENCES public.sla_violations(violation_id),
    amount_usd DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sla_contracts_org ON public.sla_contracts(org_id);
CREATE INDEX idx_sla_violations_org ON public.sla_violations(org_id, created_at DESC);
CREATE INDEX idx_sla_violations_contract ON public.sla_violations(contract_id);
CREATE INDEX idx_sla_refunds_org ON public.sla_refunds(org_id);

-- RLS
ALTER TABLE public.sla_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sla_violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sla_refunds ENABLE ROW LEVEL SECURITY;
