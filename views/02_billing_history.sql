-- Billing History and Invoice Summary View
-- Version: 31.0

CREATE OR REPLACE VIEW public.billing_history_view AS
SELECT
    i.invoice_id,
    i.org_id,
    o.company_name,
    i.invoice_number,
    i.issue_date,
    i.due_date,
    i.total_usd,
    i.status,
    i.paid_at,
    i.payment_method,
    json_agg(json_build_object('description', ii.description, 'quantity', ii.quantity, 'total_usd', ii.total_usd)) as line_items
FROM public.invoices i
LEFT JOIN public.organizations o ON i.org_id = o.org_id
LEFT JOIN public.invoice_items ii ON i.invoice_id = ii.invoice_id
GROUP BY i.invoice_id, i.org_id, o.company_name, i.invoice_number, i.issue_date, i.due_date, i.total_usd, i.status, i.paid_at, i.payment_method
ORDER BY i.issue_date DESC;

-- Outstanding invoices view
CREATE OR REPLACE VIEW public.outstanding_invoices AS
SELECT
    i.invoice_id,
    i.org_id,
    o.company_name,
    i.invoice_number,
    i.issue_date,
    i.due_date,
    i.total_usd,
    EXTRACT(DAY FROM (NOW() - i.due_date)) as days_overdue
FROM public.invoices i
JOIN public.organizations o ON i.org_id = o.org_id
WHERE i.status = 'pending' AND i.due_date < NOW()
ORDER BY i.due_date ASC;
