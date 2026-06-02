-- PayPal Transactions and Subscriptions Tables
-- Version: 31.0

-- PayPal transactions
CREATE TABLE IF NOT EXISTS public.paypal_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id TEXT,
    capture_id TEXT UNIQUE,
    user_id TEXT NOT NULL,
    amount_usd DECIMAL(12, 4) NOT NULL,
    currency TEXT DEFAULT 'USD',
    payer_email TEXT,
    payer_name TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    refund_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    webhook_processed_at TIMESTAMP WITH TIME ZONE
);

-- PayPal subscriptions
CREATE TABLE IF NOT EXISTS public.paypal_subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled', 'expired')),
    start_date TIMESTAMP WITH TIME ZONE,
    next_billing_time TIMESTAMP WITH TIME ZONE,
    last_payment_amount DECIMAL(12, 4),
    last_payment_time TIMESTAMP WITH TIME ZONE,
    cancel_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE
);

-- PayPal plans (for subscriptions)
CREATE TABLE IF NOT EXISTS public.paypal_plans (
    plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    amount_usd DECIMAL(12, 4) NOT NULL,
    currency TEXT DEFAULT 'USD',
    interval_type TEXT CHECK (interval_type IN ('DAY', 'WEEK', 'MONTH', 'YEAR')),
    interval_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default plans
INSERT INTO public.paypal_plans (plan_id, plan_name, amount_usd, currency, interval_type, interval_count) VALUES
    ('P-1', 'Developer Monthly', 49.00, 'USD', 'MONTH', 1),
    ('P-2', 'Business Monthly', 499.00, 'USD', 'MONTH', 1),
    ('P-3', 'Enterprise Monthly', 2499.00, 'USD', 'MONTH', 1),
    ('P-4', 'Developer Yearly', 470.40, 'USD', 'YEAR', 1),
    ('P-5', 'Business Yearly', 4790.40, 'USD', 'YEAR', 1)
ON CONFLICT (plan_id) DO NOTHING;

-- Indexes
CREATE INDEX idx_paypal_transactions_user ON public.paypal_transactions(user_id, created_at DESC);
CREATE INDEX idx_paypal_transactions_capture ON public.paypal_transactions(capture_id);
CREATE INDEX idx_paypal_transactions_status ON public.paypal_transactions(status);
CREATE INDEX idx_paypal_subscriptions_user ON public.paypal_subscriptions(user_id);
CREATE INDEX idx_paypal_subscriptions_status ON public.paypal_subscriptions(status);
CREATE INDEX idx_paypal_plans_active ON public.paypal_plans(is_active);

-- RLS Policies
ALTER TABLE public.paypal_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paypal_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paypal_plans ENABLE ROW LEVEL SECURITY;
