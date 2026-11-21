# Decisions and roadmap

[Project overview](../README.md)

**Named business examples; fictional records.** The public names provide context for this independent demonstration. Every order and calculated financial or delivery measure is synthetic. The examples do not establish client financial impact or work Ziana Bennett performed for each business. [Business context and sources](business-context.md).

## Historical direction

SupplyBistro's reporting discussion clarified that AI should help the internal team create canned reports. An interactive customer feature that generated SQL on each request raised a different variable-cost question. The direction discussed at that stage focused on recurring report definitions and the information required to build them.

The planning sequence included discovery, a prototype with 2–3 reports, a possible MVP with 8–10 reports, and integration. These were planned stages, not verified delivery milestones. This portfolio extension implements three fictional reports as a separate demonstration.

## Decisions in the portfolio implementation

| Decision | Reason | Consequence |
| --- | --- | --- |
| Execute reviewed SQL definitions | The same inputs should produce the same answers | No runtime AI dependency or generation claim |
| Keep SQL in separate readable files | A reviewer can compare each definition with its requirements | SQL changes remain visible in version history |
| Use Python standard library and in-memory SQLite | Make the project easy to reproduce without a service account | The project is a local analytical example, not an application backend |
| Store money as integer cents | Totals must reconcile exactly | Currency formatting happens after aggregation |
| Model receipt and cancellation dates | An earlier snapshot should not inherit later status changes | Only this model's simple one-event lifecycle is supported |
| Use order counts to weight delivery rates | Supplier percentages can have different denominators | Overall reliability must be recomputed from counts |
| Generate JSON, Markdown, and SVG together | Keep human and machine-readable results consistent | Regeneration updates all output formats from one report object |
| Use public business names as labeled demonstration examples | Connect the exercise to a documented commercial context | All operational records remain fictional; public relationships and their limits are cited separately |

## Where AI fits

AI assistance was used to develop this portfolio extension. The executable model deliberately separates authoring assistance from report execution. A team could use a model to propose SQL from approved field definitions and a report specification, then inspect the proposed SQL and validate it against examples before storing the approved query.

This is a development workflow. The repository does not contain a model integration, execute generated text, or demonstrate that AI produces correct SQL automatically. The independent requirements and boundary tests provide a way to review proposed query changes.

## Options considered for a real next stage

| Option | Useful when | Remaining question |
| --- | --- | --- |
| Reusable queries with filters | Questions recur and definitions are stable | Which report set covers the most valuable recurring work? |
| Internal assisted query drafting | Report development is the bottleneck | How much review does a draft query require? |
| Customer natural-language querying | Users need flexible questions beyond predefined reports | How would cost, permissions, query validation, and ambiguous requests be handled? |

No cost saving is estimated because the exercise contains no observed usage volumes, provider prices, or production baseline.

## Practical next steps

1. **Validate demand.** Review recurring requests with the actual users and select a small report set. Record the decision each report supports and the cost of a wrong answer.
2. **Map the schema.** Confirm identifiers, join cardinality, currencies, date semantics, and status history. Check whether partial deliveries or cancellations affect the measures.
3. **Validate representative examples.** Compare expected outputs with approved data and a subject-matter review. Include empty periods, duplicates, cancellations, and period boundaries.
4. **Integrate with a clear owner.** Decide who can run each report, who approves definition changes, how slow or failing queries are observed, and what user acceptance means.

An expansion toward 8–10 reports should follow evidence about demand and review effort. Report count by itself does not demonstrate useful coverage.

