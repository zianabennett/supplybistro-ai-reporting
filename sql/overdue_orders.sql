-- An order is open at the snapshot if it has been booked and neither a
-- receipt nor a cancellation has happened yet. Due today is not overdue.
SELECT
    po.order_id,
    po.supplier_id,
    s.supplier_label,
    po.promised_date,
    CAST(julianday(:as_of) - julianday(po.promised_date) AS INTEGER)
        AS days_overdue,
    po.order_value_cents
FROM purchase_orders AS po
JOIN suppliers AS s ON s.supplier_id = po.supplier_id
WHERE po.order_date <= :as_of
  AND po.promised_date < :as_of
  AND (po.received_date IS NULL OR po.received_date > :as_of)
  AND (po.cancelled_date IS NULL OR po.cancelled_date > :as_of)
ORDER BY days_overdue DESC, po.order_id;

