-- Revenue Analytics Dashboard View
-- Version: 31.0

CREATE OR REPLACE VIEW public.revenue_analytics AS
SELECT
    DATE(mt.created_at) as date,
    COUNT(mt.tx_id) as transaction_count,
    SUM(mt.amount_usd) as total_revenue_usd,
    SUM(mt.cashback_usd) as total_cashback_usd,
    AVG(mt.amount_usd) as avg_transaction_usd,
    COUNT(DISTINCT mt.user_id) as unique_customers,
    COUNT(DISTINCT mt.merchant_id) as active_merchants
FROM public.micro_transactions mt
WHERE mt.status = 'completed'
GROUP BY DATE(mt.created_at)
ORDER BY date DESC;

-- Monthly revenue summary
CREATE OR REPLACE VIEW public.monthly_revenue_summary AS
SELECT
    DATE_TRUNC('month', mt.created_at) as month,
    COUNT(mt.tx_id) as total_transactions,
    SUM(mt.amount_usd) as total_revenue_usd,
    SUM(mt.gross_amount_usd) as gross_volume_usd,
    SUM(mt.cashback_usd) as total_cashback_usd,
    COUNT(DISTINCT mt.user_id) as unique_customers,
    COUNT(DISTINCT mt.merchant_id) as active_merchants,
    COUNT(DISTINCT CASE WHEN mt.payment_method = 'mobile_money' THEN mt.tx_id END) as mobile_money_tx,
    COUNT(DISTINCT CASE WHEN mt.payment_method = 'crypto' THEN mt.tx_id END) as crypto_tx
FROM public.micro_transactions mt
WHERE mt.status = 'completed'
GROUP BY DATE_TRUNC('month', mt.created_at)
ORDER BY month DESC;
