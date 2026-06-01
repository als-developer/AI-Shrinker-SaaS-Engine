-- Customer Support Tickets System
-- Version: 31.0

-- Support tickets
CREATE TABLE IF NOT EXISTS public.support_tickets (
    ticket_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    org_id UUID REFERENCES public.organizations(org_id),
    ticket_number TEXT UNIQUE,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT CHECK (category IN ('billing', 'technical', 'api', 'account', 'security', 'other')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to UUID REFERENCES public.user_profiles(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ticket replies
CREATE TABLE IF NOT EXISTS public.ticket_replies (
    reply_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES public.support_tickets(ticket_id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.user_profiles(id),
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false,
    attachments JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ticket attachments
CREATE TABLE IF NOT EXISTS public.ticket_attachments (
    attachment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES public.support_tickets(ticket_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    storage_path TEXT,
    uploaded_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tickets_user ON public.support_tickets(user_id, created_at DESC);
CREATE INDEX idx_tickets_org ON public.support_tickets(org_id);
CREATE INDEX idx_tickets_status ON public.support_tickets(status);
CREATE INDEX idx_tickets_priority ON public.support_tickets(priority);
CREATE INDEX idx_ticket_replies_ticket ON public.ticket_replies(ticket_id, created_at);

-- RLS
ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket_attachments ENABLE ROW LEVEL SECURITY;
