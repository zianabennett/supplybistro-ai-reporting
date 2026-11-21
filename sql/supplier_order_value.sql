-- Purchase order value booked in the requested period and still valid as of
-- the snapshot date. Receipt is not required. This is not a payment measure.
SELECT
    po.supplier_id,
    s.supplier_label,
    COUNT(*) AS order_count,
    SUM(po.order_value_cents) AS order_value_cents
FROM purchase_orders AS po
JOIN suppliers AS s ON s.supplier_id = po.supplier_id
WHERE po.order_date >= :period_start
  AND po.order_date < :period_end
  AND po.order_date <= :as_of
  AND (po.cancelled_date IS NULL OR po.cancelled_date > :as_of)
GROUP BY po.supplier_id, s.supplier_label
ORDER BY order_value_cents DESC, po.supplier_id;

