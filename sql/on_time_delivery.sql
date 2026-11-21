-- The reporting month follows receipt date, not the order's booking date.
-- A receipt on its promised date is on time. Aggregate counts are retained
-- so the overall rate can be weighted by orders, not averaged by supplier.
SELECT
    po.supplier_id,
    s.supplier_label,
    COUNT(*) AS received_order_count,
    SUM(CASE WHEN po.received_date <= po.promised_date THEN 1 ELSE 0 END)
        AS on_time_order_count
FROM purchase_orders AS po
JOIN suppliers AS s ON s.supplier_id = po.supplier_id
WHERE po.received_date >= :period_start
  AND po.received_date < :period_end
  AND po.received_date <= :as_of
GROUP BY po.supplier_id, s.supplier_label
ORDER BY po.supplier_id;

