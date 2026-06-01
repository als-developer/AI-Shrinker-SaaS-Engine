-- Developer API Key Analytics View
-- Version: 31.0

CREATE OR REPLACE VIEW public.developer_analytics AS
SELECT
    d.developer_id,
    u.email,
    u.full_name,
    COUNT(DISTINCT d.key_hash) as total_keys,
    COUNT(CASE WHEN d.is_active THEN 1 END) as active_keys,
    SUM(aul.total_requests) as total_api_calls,
    SUM(aul.total_revenue_usd) as total_revenue_usd,
    MAX(aul.last_activity) as last_active
FROM public.developer_api_keys d
JOIN public.user_profiles u ON d.developer_id = u.id
LEFT JOIN (
    SELECT 
        key_hash,
        COUNT(*) as total_requests,
        SUM(amount_usd) as total_revenue_usd,
        MAX(created_at) as last_activity
    FROM public.api_usage_logs aul
    GROUP BY key_hash
) aul ON d.key_hash = aul.key_hash
GROUP BY d.developer_id, u.email, u.full_name
ORDER BY total_api_calls DESC;

-- Rate limit violation summary
CREATE OR REPLACE VIEW public.rate_limit_summary AS
SELECT
    DATE(rlv.created_at) as date,
    rlv.api_key_hash,
    COUNT(*) as violation_count,
    COUNT(DISTINCT rlv.endpoint) as endpoints_affected,
    MIN(rlv.created_at) as first_violation,
    MAX(rlv.created_at) as last_violation
FROM public.rate_limit_violations rlv
GROUP BY DATE(rlv.created_at), rlv.api_key_hash
ORDER BY date DESC, violation_count DESC;
