-- Department and Team Hierarchy Tables
-- Version: 31.0

-- Extended departments with hierarchy
CREATE TABLE IF NOT EXISTS public.department_hierarchy (
    dept_id UUID PRIMARY KEY REFERENCES public.departments(dept_id) ON DELETE CASCADE,
    parent_dept_id UUID REFERENCES public.departments(dept_id),
    hierarchy_level INTEGER DEFAULT 0,
    path LTREE,  -- PostgreSQL ltree extension for hierarchical queries
    budget_rollup BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Department budget allocation history
CREATE TABLE IF NOT EXISTS public.department_budget_history (
    budget_history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dept_id UUID REFERENCES public.departments(dept_id) ON DELETE CASCADE,
    month_year DATE NOT NULL,
    allocated_budget_usd DECIMAL(12, 2),
    consumed_budget_usd DECIMAL(12, 2),
    rollover_from_previous DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team member assignments
CREATE TABLE IF NOT EXISTS public.team_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    dept_id UUID REFERENCES public.departments(dept_id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable ltree extension if not exists
CREATE EXTENSION IF NOT EXISTS ltree;

-- Indexes
CREATE INDEX idx_dept_hierarchy_parent ON public.department_hierarchy(parent_dept_id);
CREATE INDEX idx_dept_hierarchy_path ON public.department_hierarchy USING GIST(path);
CREATE INDEX idx_dept_budget_month ON public.department_budget_history(dept_id, month_year);
CREATE INDEX idx_team_assignments_user ON public.team_assignments(user_id);
CREATE INDEX idx_team_assignments_dept ON public.team_assignments(dept_id);

-- RLS
ALTER TABLE public.department_hierarchy ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.department_budget_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_assignments ENABLE ROW LEVEL SECURITY;
