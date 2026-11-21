# Method and data

[Project overview](../README.md)

## Reproduce the published example

The repository uses Python 3.9 or later and the standard-library `sqlite3` module. No third-party Python package is required.

```sh
python3 generate_data.py
python3 run.py
python3 -m unittest discover -s tests -v
```

The first command reconstructs the committed [fictional dataset](../data/synthetic_purchase_orders.json). The second produces the committed [report results](../results/report_results.json), [summary](../results/summary.md), and SVG charts. Data generation uses fixed arithmetic and fixed boundary records; it does not use randomness, today's date, or a network connection. Running the same commands with the same inputs produces the same output content.

The data is loaded into an in-memory SQLite database for each run. SQL receives date parameters separately from the query text. The database is closed after the three queries complete.

## Dataset construction

The fixture contains 60 mechanically generated orders and 12 explicit boundary records, spread across four fictional supplier labels. It includes orders before, during, and after September 2026. The distribution is designed to exercise rules, not to resemble a measured business population. Supplier performance comparisons have no real-world meaning.

| Explicit record | Purpose |
| --- | --- |
| PO061 | August booking received in September |
| PO062 | Booking on the reporting period's lower boundary |
| PO063 | September 30 booking received after the snapshot |
| PO064 | October 1 booking outside the September period |
| PO065 | Order due on the snapshot date |
| PO066 | Open order exactly one day overdue |
| PO067 | Cancellation before the snapshot |
| PO068 | Receipt exactly on the promised date |
| PO069 | Early receipt |
| PO070 | Late receipt |
| PO071 | Cancellation after the default snapshot |
| PO072 | September booking with an October receipt |

The complete field contract is in the [data dictionary](../data/data_dictionary.json). Each value belongs to the order, not an order line. Amounts use integer cents, avoiding the repeated-total problem that can occur when an order-level value is joined to several line items.

## Historical state in the fictional model

An order exists at a snapshot only if its order date has arrived. It becomes received or cancelled when the corresponding event date arrives. Otherwise it remains open. A later event does not retroactively change the earlier snapshot. For example, PO071 is open and overdue on September 30, then cancelled by October 3.

This is a deliberately small event model. It allows a single receipt or cancellation per order and prohibits both together. A real purchasing system might need multiple receipt events, revisions, returns, and cancellation reversals. Those events would change the data model and acceptance criteria.

## Validation approach

The tests use hand-authored miniature datasets with independently calculable answers. They check financial period boundaries, exact-cent totals, empty rates, weighted denominators, and snapshot behavior after later events. The committed 72-order fixture is also checked for deterministic regeneration and validated before loading.

The default model produces 42 qualifying September orders with a value of $112,956.48. The open backlog contains 9 overdue orders worth $20,295.26, including older orders outside September. Delivery performance includes 31 September receipts, of which 24 are on time. The 77.42% rate follows receipt counts, not the purchase-order-value population.

These populations intentionally differ because they answer different questions. The [requirements](requirements.md) define each population before implementation.

