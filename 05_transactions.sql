-- Payment and Transaction Tables
-- Version: 31.0

-- Micro-transactions ledger
CREATE TABLE IF NOT EXISTS public.micro_transactions (
    tx_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    amount_usd DECIMAL(12, 6) NOT NULL,
    gross_amount_usd DECIMAL(12, 6) NOT NULL,
    cashback_usd DECIMAL(12, 6) DEFAULT 0,
    currency_code TEXT DEFAULT 'USD',
    fiat_amount DECIMAL(15, 2),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_method TEXT CHECK (payment_method IN ('mobile_money', 'crypto', 'wallet_balance', 'card')),
    provider_reference TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Merchant accounts
CREATE TABLE IF NOT EXISTS public.merchant_accounts (
    merchant_id TEXT PRIMARY KEY,
    org_id UUID REFERENCES public.organizations(org_id),
    company_name TEXT NOT NULL,
    domain_url TEXT,
    api_key_hash TEXT,
    webhook_url TEXT,
    webhook_secret TEXT,
    settlement_method TEXT DEFAULT 'bank_transfer',
    settlement_details JSONB,
    payout_threshold_usd DECIMAL(12, 2) DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payout claims
CREATE TABLE IF NOT EXISTS public.payout_claims (
    payout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id TEXT REFERENCES public.merchant_accounts(merchant_id),
    amount_usd DECIMAL(12, 2) NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_micro_tx_user ON public.micro_transactions(user_id);
CREATE INDEX idx_micro_tx_merchant ON public.micro_transactions(merchant_id);
CREATE INDEX idx_micro_tx_created ON public.micro_transactions(created_at);
CREATE INDEX idx_merchant_org ON public.merchant_accounts(org_id);

-- RLS
ALTER TABLE public.micro_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.merchant_accounts ENABLE ROW LEVEL SECURITY;
