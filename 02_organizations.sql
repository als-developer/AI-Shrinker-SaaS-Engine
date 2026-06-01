-- Organizations and Multi-Tenant Tables
-- Version: 31.0

-- Organizations table
CREATE TABLE IF NOT EXISTS public.organizations (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    owner_id UUID REFERENCES public.user_profiles(id),
    billing_email TEXT,
    phone_number TEXT,
    address TEXT,
    city TEXT,
    country TEXT DEFAULT 'Tanzania',
    tier TEXT DEFAULT 'startup' CHECK (tier IN ('free', 'startup', 'business', 'enterprise')),
    billing_status TEXT DEFAULT 'active' CHECK (billing_status IN ('active', 'past_due', 'suspended', 'cancelled')),
    max_monthly_credits DECIMAL(12, 4) DEFAULT 1000,
    credits_used DECIMAL(12, 4) DEFAULT 0,
    subscription_start_date DATE,
    subscription_end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Organization members (team)
CREATE TABLE IF NOT EXISTS public.org_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'manager', 'member', 'viewer')),
    department TEXT,
    invited_by UUID REFERENCES public.user_profiles(id),
    invitation_status TEXT DEFAULT 'pending' CHECK (invitation_status IN ('pending', 'accepted', 'declined')),
    joined_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- Departments within organizations
CREATE TABLE IF NOT EXISTS public.departments (
    dept_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.organizations(org_id) ON DELETE CASCADE,
    department_name TEXT NOT NULL,
    budget_cap_usd DECIMAL(12, 4) DEFAULT 500,
    credits_consumed_usd DECIMAL(12, 4) DEFAULT 0,
    manager_id UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_organizations_owner ON public.organizations(owner_id);
CREATE INDEX idx_org_members_org ON public.org_members(org_id);
CREATE INDEX idx_org_members_user ON public.org_members(user_id);
CREATE INDEX idx_departments_org ON public.departments(org_id);

-- RLS Policies
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.org_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;

-- Functions
CREATE OR REPLACE FUNCTION is_org_member(org_id UUID, user_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS(SELECT 1 FROM public.org_members WHERE org_members.org_id = $1 AND org_members.user_id = $2);
$$ LANGUAGE sql SECURITY DEFINER;
