-- Compliance Audit Logging Tables
-- Version: 31.0

-- Main audit log table (immutable)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id),
    org_id UUID REFERENCES public.organizations(org_id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id TEXT,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Security events log
CREATE TABLE IF NOT EXISTS public.security_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT CHECK (event_type IN ('login', 'logout', 'failed_login', 'api_key_created', 'api_key_revoked', 'permission_change', 'sla_violation')),
    severity TEXT CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    user_id UUID REFERENCES public.user_profiles(id),
    org_id UUID REFERENCES public.organizations(org_id),
    ip_address INET,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data access logs (GDPR compliance)
CREATE TABLE IF NOT EXISTS public.data_access_logs (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id),
    data_subject_email TEXT,
    access_type TEXT CHECK (access_type IN ('view', 'export', 'delete', 'rectify')),
    data_scope JSONB,
    consent_provided BOOLEAN,
    request_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user ON public.audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_org ON public.audit_logs(org_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX idx_security_events_type ON public.security_events(event_type, created_at DESC);
CREATE INDEX idx_security_events_severity ON public.security_events(severity);
CREATE INDEX idx_data_access_logs_user ON public.data_access_logs(user_id);

-- RLS (Restricted access - only admins)
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.security_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_access_logs ENABLE ROW LEVEL SECURITY;

-- Audit log retention policy (90 days)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM public.audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
    DELETE FROM public.security_events WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
