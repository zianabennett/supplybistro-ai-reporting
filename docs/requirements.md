# Report requirements

[Project overview](../README.md)

## Goal and shared contract

Create a small report set that a business user can interpret consistently and a technical teammate can validate independently. The fictional model contains one row per purchase order, one currency, and order-level values. Query execution accepts an inclusive period start, an exclusive period end, and an inclusive snapshot date.

The default period is September 1 through September 30, 2026, expressed as `2026-09-01 <= date < 2026-10-01`. The snapshot is September 30. An event dated after the snapshot has not happened yet for that report. This remains true even when the complete fixture contains later events.

The portfolio uses the following user stories to make the reporting intent concrete. They are specifications for this implementation.

## Purchase order value by supplier

**User story.** As a purchasing reviewer, I want to compare the value booked with each supplier during a selected period, allowing me to identify where a review of purchasing activity should begin.

Use order date to select the period. Exclude orders booked after the snapshot and orders cancelled on or before the snapshot. A later cancellation does not change the earlier snapshot. Received and still-open orders both contribute. An order contributes its full value exactly once.

Output supplier ID, supplier label, order count, and integer-cent order value. Sort by descending value, using supplier ID to break ties. The final total is the sum of the supplier results. This measure is a snapshot of valid purchase order value, not payments, recognized expense, or invoiced spend.

| Case | Expected behavior |
| --- | --- |
| Order booked on September 1 | Included if valid at the snapshot |
| Order booked on October 1 | Excluded from September |
| Order cancelled September 12 | Excluded at September 30 |
| Order cancelled October 2 | Included at September 30 and excluded at October 3 |
| Two qualifying values of 1 cent and 2 cents | Total is exactly 3 cents |

Implementation: [supplier_order_value.sql](../sql/supplier_order_value.sql).

## Open overdue orders

**User story.** As an operations reviewer, I want an ordered list of outstanding purchase orders that have passed their promised dates, allowing me to investigate the longest outstanding items first.

An order must exist by the snapshot, have a promised date earlier than that date, and have neither a receipt nor cancellation on or before it. The selected monthly period does not limit the backlog. A purchase order from August can remain overdue in September.

Output order ID, supplier, promised date, whole days overdue, and order value. Sort by days overdue descending, then order ID. The total value represents the full value of those open orders because partial receipt is outside this model.

| Case | Expected behavior |
| --- | --- |
| Promised September 29 and open September 30 | Included, one day overdue |
| Promised September 30 | Excluded on September 30 |
| Received October 2 | Still open at September 30 |
| Cancelled October 2 | Still open at September 30 |
| Received or cancelled September 30 | No longer open at that snapshot |
| Booked after the snapshot | Excluded |

Implementation: [overdue_orders.sql](../sql/overdue_orders.sql).

## On time delivery

**User story.** As an operations reviewer, I want the proportion of completed deliveries that met their promised dates, allowing me to assess receipt reliability separately from the open-order backlog.

Use receipt date to select the period and require that receipt to occur on or before the snapshot. An August order received in September belongs to September delivery performance. A September order received in October does not. A receipt on or before its promised date is on time.

Output received count, on-time count, and rate for each supplier with eligible receipts. The overall rate is `100 × all on-time receipts / all eligible receipts`. It is not the unweighted average of supplier rates. Round display percentages to two decimal places. Preserve the counts to allow recalculation.

| Case | Expected behavior |
| --- | --- |
| Received exactly on the promised date | On time |
| Received one day early | On time |
| Received one day late | Late |
| Open order with no receipt | Excluded from the denominator |
| No eligible receipts | Zero counts and a JSON `null` rate |
| Supplier A is 1/1 and Supplier B is 0/3 | Overall rate is 25%, not 50% |

Implementation: [on_time_delivery.sql](../sql/on_time_delivery.sql).

## Input quality and acceptance

Reject duplicate or empty order IDs, unknown suppliers, malformed calendar dates, negative or noninteger cent amounts, unsupported currencies, and events before order creation. The simple lifecycle cannot contain both receipt and cancellation for the same order. This rule is explicit; a richer returns or reversal model would require additional event types.

A report is accepted when the [boundary tests](../tests/test_reporting.py) pass, the displayed totals reconcile to the JSON output, and each included measure answers its stated business question. A successful fictional example is evidence about this implementation, not a substitute for validating an employer's actual data.

