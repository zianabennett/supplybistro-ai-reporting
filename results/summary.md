# Reporting results

[Project overview](../README.md) · [Machine-readable results](report_results.json)

**Named business examples; all orders, amounts, dates and delivery metrics are fictional.** These figures do not describe the named businesses' actual finances or delivery performance. [Read the business context and source distinctions](../docs/business-context.md).

Period **2026-09-01 to 2026-10-01**, with the end date excluded. Snapshot **2026-09-30**. The complete fixture contains **72 fictional orders**.

## Measures

| Measure | Computed result |
| --- | ---: |
| Qualifying purchase orders | 42 |
| Qualifying purchase order value | $112,956.48 |
| Open overdue orders at the snapshot | 9 |
| Value of open overdue orders | $20,295.26 |
| Received orders in the period | 31 |
| Received on time | 24 |
| On-time delivery rate | 77.42% |

The order-value measure uses booking date. The delivery measure uses receipt date. The overdue report uses the snapshot date and includes older open orders, regardless of the selected reporting month.

## Fictional purchase order value by named example

![Fictional purchase order value by named business example](supplier_order_value.svg)

| Named business example | Fictional orders | Fictional order value |
| --- | ---: | ---: |
| Grow The Earth | 12 | $34,865.66 |
| Staccato Bakery | 12 | $31,198.34 |
| Good Four Season Trading | 9 | $24,388.28 |
| Abstinence Spirits | 9 | $22,504.20 |

## Fictional open overdue orders

| Fictional order | Named business example | Fictional promised date | Days overdue | Fictional order value |
| --- | --- | --- | ---: | ---: |
| PO001 | Staccato Bakery | 2026-08-30 | 31 | $579.19 |
| PO031 | Grow The Earth | 2026-09-05 | 25 | $2,954.89 |
| PO049 | Staccato Bakery | 2026-09-13 | 17 | $4,380.31 |
| PO019 | Grow The Earth | 2026-09-14 | 16 | $2,004.61 |
| PO007 | Grow The Earth | 2026-09-16 | 14 | $1,054.33 |
| PO071 | Grow The Earth | 2026-09-20 | 10 | $2,400.00 |
| PO037 | Staccato Bakery | 2026-09-22 | 8 | $3,430.03 |
| PO010 | Abstinence Spirits | 2026-09-28 | 2 | $1,291.90 |
| PO066 | Abstinence Spirits | 2026-09-29 | 1 | $2,200.00 |

## Fictional on-time delivery

![Fictional on-time delivery by named business example](delivery_performance.svg)

| Named business example | Fictional receipts | Fictional on-time receipts | Fictional rate |
| --- | ---: | ---: | ---: |
| Staccato Bakery | 9 | 9 | 100.00% |
| Abstinence Spirits | 8 | 4 | 50.00% |
| Grow The Earth | 7 | 7 | 100.00% |
| Good Four Season Trading | 7 | 4 | 57.14% |

The overall rate is calculated from all eligible orders. It is not an average of supplier percentages. Suppliers with no receipts have no delivery rate and are omitted from that chart.

## Reading the output

These measures verify the behavior of a fictional reporting model. The named examples give the demonstration public business context; their amounts, rankings, overdue orders and delivery rates have no real-world performance meaning. They do not establish actual client financial impact or work Ziana Bennett performed for each business. In a real report, the value ranking and overdue list would guide investigation using validated operational data.

Regenerate this folder with `python3 run.py`. Its JSON, tables, and charts are produced from the same report objects.
