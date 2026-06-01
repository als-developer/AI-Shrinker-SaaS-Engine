-- Invoice and Billing Tables
-- Version: 31.0

-- Invoices table
CREATE TABLE IF NOT EXISTS public.invoices (
    invoice_id TEXT PRIMARY KEY,
    org_id UUID REFERENCES public.organizations(org_id) ON DELETE CASCADE,
    invoice_number TEXT UNIQUE,
    billing_period TEXT,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    subtotal_usd DECIMAL(12, 2) NOT NULL,
    tax_usd DECIMAL(12, 2) DEFAULT 0,
    total_usd DECIMAL(12, 2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled', 'refunded')),
    payment_method TEXT,
    payment_reference TEXT,
    paid_at TIMESTAMP WITH TIME ZONE,
    invoice_pdf_url TEXT,
    line_items JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment records
CREATE TABLE IF NOT EXISTS public.payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id TEXT REFERENCES public.invoices(invoice_id),
    org_id UUID REFERENCES public.organizations(org_id),
    amount_usd DECIMAL(12, 2) NOT NULL,
    payment_method TEXT CHECK (payment_method IN ('card', 'bank_transfer', 'crypto', 'mobile_money', 'wallet')),
    payment_provider TEXT,
    provider_transaction_id TEXT,
    status TEXT DEFAULT 'pending',
    metadata JSONB,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoice items
CREATE TABLE IF NOT EXISTS public.invoice_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id TEXT REFERENCES public.invoices(invoice_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price_usd DECIMAL(12, 4) NOT NULL,
    total_usd DECIMAL(12, 4) NOT NULL,
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_invoices_org ON public.invoices(org_id, created_at DESC);
CREATE INDEX idx_invoices_status ON public.invoices(status);
CREATE INDEX idx_invoices_date ON public.invoices(issue_date);
CREATE INDEX idx_payments_invoice ON public.payments(invoice_id);
CREATE INDEX idx_payments_org ON public.payments(org_id);

-- RLS
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invoice_items ENABLE ROW LEVEL SECURITY;
