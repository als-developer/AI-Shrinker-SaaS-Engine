-- System Health and Performance View
-- Version: 31.0

CREATE OR REPLACE VIEW public.system_health_dashboard AS
SELECT
    node_id,
    region,
    AVG(cpu_percent) as avg_cpu,
    AVG(memory_used_mb) as avg_memory_mb,
    AVG(requests_per_second) as avg_rps,
    AVG(avg_latency_ms) as avg_latency_ms,
    AVG(error_rate) as avg_error_rate,
    MODE() WITHIN GROUP (ORDER BY status) as most_common_status,
    MAX(collected_at) as last_heartbeat
FROM public.node_telemetry
WHERE collected_at > NOW() - INTERVAL '1 hour'
GROUP BY node_id, region
ORDER BY region, node_id;

-- SLA compliance dashboard
CREATE OR REPLACE VIEW public.sla_compliance_dashboard AS
SELECT
    o.org_id,
    o.company_name,
    s.sla_tier,
    s.uptime_guarantee,
    COALESCE(daily.avg_uptime, 100) as current_uptime,
    CASE 
        WHEN COALESCE(daily.avg_uptime, 100) >= s.uptime_guarantee THEN 'Compliant'
        ELSE 'Violated'
    END as compliance_status,
    COUNT(v.violation_id) as violation_count_ytd,
    SUM(v.refund_amount_usd) as total_refunds_ytd
FROM public.organizations o
LEFT JOIN public.sla_contracts s ON o.org_id = s.org_id AND s.effective_from <= NOW() AND (s.effective_to IS NULL OR s.effective_to >= NOW())
LEFT JOIN (
    SELECT org_id, AVG(uptime_percentage) as avg_uptime
    FROM public.daily_metrics_summary dms
    WHERE dms.date > NOW() - INTERVAL '30 days'
    GROUP BY org_id
) daily ON o.org_id = daily.org_id
LEFT JOIN public.sla_violations v ON o.org_id = v.org_id AND v.created_at > DATE_TRUNC('year', NOW())
GROUP BY o.org_id, o.company_name, s.sla_tier, s.uptime_guarantee, daily.avg_uptime
ORDER BY compliance_status, o.company_name;
