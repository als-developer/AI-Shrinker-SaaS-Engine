-- API Usage Statistics View
-- Version: 31.0

CREATE OR REPLACE VIEW public.api_usage_stats AS
SELECT
    DATE(created_at) as date,
    endpoint,
    COUNT(*) as request_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT org_id) as unique_orgs,
    AVG(response_time_ms) as avg_response_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_ms,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    ROUND(100.0 * SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
FROM public.api_usage_logs
GROUP BY DATE(created_at), endpoint
ORDER BY date DESC, request_count DESC;

-- Top users by usage
CREATE OR REPLACE VIEW public.top_api_users AS
SELECT
    u.email,
    u.full_name,
    o.company_name,
    COUNT(aul.usage_id) as total_requests,
    SUM(CASE WHEN aul.status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    AVG(aul.response_time_ms) as avg_response_ms,
    MAX(aul.created_at) as last_active
FROM public.api_usage_logs aul
JOIN public.user_profiles u ON aul.user_id = u.id
LEFT JOIN public.org_members om ON u.id = om.user_id
LEFT JOIN public.organizations o ON om.org_id = o.org_id
WHERE aul.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.email, u.full_name, o.company_name
ORDER BY total_requests DESC
LIMIT 100;
