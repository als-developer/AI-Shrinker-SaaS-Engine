-- Customer Wallet and Balance Tables
-- Version: 31.0

-- Customer wallets (for micro-transactions)
CREATE TABLE IF NOT EXISTS public.customer_wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,  -- External customer identifier
    org_id UUID REFERENCES public.organizations(org_id),
    balance_usd DECIMAL(12, 6) DEFAULT 0,
    balance_tzs DECIMAL(15, 2) GENERATED ALWAYS AS (balance_usd * 2615.50) STORED,
    currency TEXT DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, org_id)
);

-- Wallet transactions
CREATE TABLE IF NOT EXISTS public.wallet_transactions (
    tx_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES public.customer_wallets(wallet_id) ON DELETE CASCADE,
    amount_usd DECIMAL(12, 6) NOT NULL,
    amount_tzs DECIMAL(15, 2),
    transaction_type TEXT CHECK (transaction_type IN ('deposit', 'withdrawal', 'payment', 'refund', 'cashback')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    reference TEXT,
    description TEXT,
    metadata JSONB,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deposits record
CREATE TABLE IF NOT EXISTS public.deposits (
    deposit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES public.customer_wallets(wallet_id),
    amount_usd DECIMAL(12, 6) NOT NULL,
    method TEXT CHECK (method IN ('mobile_money', 'bank_transfer', 'crypto', 'card')),
    provider TEXT,
    provider_reference TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_wallets_user ON public.customer_wallets(user_id);
CREATE INDEX idx_wallet_tx_wallet ON public.wallet_transactions(wallet_id);
CREATE INDEX idx_wallet_tx_created ON public.wallet_transactions(created_at);
CREATE INDEX idx_deposits_wallet ON public.deposits(wallet_id);

-- RLS
ALTER TABLE public.customer_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wallet_transactions ENABLE ROW LEVEL SECURITY;
