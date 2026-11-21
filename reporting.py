"""Deterministic reporting and presentation using the Python standard library."""

import html
import json
import sqlite3
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_NOTICE = "Named business examples; all orders, amounts, dates and delivery metrics are fictional."
ORDER_FIELDS = (
    "order_id", "supplier_id", "order_date", "promised_date", "received_date",
    "cancelled_date", "order_value_cents", "currency",
)


def iso_date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{label} must use YYYY-MM-DD")
    return parsed


def validate_dataset(dataset):
    """Reject ambiguous records before they can alter counts or denominators."""
    if not isinstance(dataset, dict) or not isinstance(dataset.get("suppliers"), list):
        raise ValueError("Dataset requires a suppliers list")
    if not isinstance(dataset.get("orders"), list):
        raise ValueError("Dataset requires an orders list")
    supplier_ids = set()
    for supplier in dataset["suppliers"]:
        sid = supplier.get("supplier_id")
        label = supplier.get("supplier_label")
        if not isinstance(sid, str) or not sid.strip() or sid in supplier_ids:
            raise ValueError("Supplier IDs must be unique nonempty strings")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"{sid} requires a supplier label")
        supplier_ids.add(sid)
    order_ids = set()
    for order in dataset["orders"]:
        if set(order) != set(ORDER_FIELDS):
            raise ValueError("Every order must use exactly the documented fields")
        oid = order["order_id"]
        if not isinstance(oid, str) or not oid.strip() or oid in order_ids:
            raise ValueError("Order IDs must be unique nonempty strings")
        order_ids.add(oid)
        if order["supplier_id"] not in supplier_ids:
            raise ValueError(f"{oid} references an unknown supplier")
        ordered = iso_date(order["order_date"], f"{oid} order_date")
        promised = iso_date(order["promised_date"], f"{oid} promised_date")
        if promised < ordered:
            raise ValueError(f"{oid} cannot be promised before it is ordered")
        if type(order["order_value_cents"]) is not int or order["order_value_cents"] < 0:
            raise ValueError(f"{oid} requires a nonnegative integer cent amount")
        if order["currency"] != "USD":
            raise ValueError(f"{oid} uses an unsupported currency")
        if order["received_date"] is not None and order["cancelled_date"] is not None:
            raise ValueError(f"{oid} cannot be both received and cancelled in this model")
        for field in ("received_date", "cancelled_date"):
            if order[field] is not None and iso_date(order[field], f"{oid} {field}") < ordered:
                raise ValueError(f"{oid} {field} cannot precede its order date")


def create_database(dataset):
    validate_dataset(dataset)
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    connection.executemany(
        "INSERT INTO suppliers VALUES (:supplier_id, :supplier_label)", dataset["suppliers"]
    )
    columns = ", ".join(ORDER_FIELDS)
    parameters = ", ".join(":" + field for field in ORDER_FIELDS)
    connection.executemany(
        f"INSERT INTO purchase_orders ({columns}) VALUES ({parameters})", dataset["orders"]
    )
    return connection


def percentage(numerator, denominator):
    if denominator == 0:
        return None
    value = Decimal(numerator) * Decimal(100) / Decimal(denominator)
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def money(cents):
    return f"${Decimal(cents) / Decimal(100):,.2f}"


def build_reports(dataset, period_start="2026-09-01", period_end="2026-10-01", as_of="2026-09-30"):
    start = iso_date(period_start, "period_start")
    end = iso_date(period_end, "period_end")
    iso_date(as_of, "as_of")
    if start >= end:
        raise ValueError("period_end must be later than period_start")
    params = {"period_start": period_start, "period_end": period_end, "as_of": as_of}
    connection = create_database(dataset)
    try:
        def query(name):
            statement = (ROOT / "sql" / name).read_text(encoding="utf-8")
            return [dict(row) for row in connection.execute(statement, params)]

        value_rows = query("supplier_order_value.sql")
        overdue_rows = query("overdue_orders.sql")
        delivery_rows = query("on_time_delivery.sql")
    finally:
        connection.close()
    for row in delivery_rows:
        row["on_time_rate_pct"] = percentage(row["on_time_order_count"], row["received_order_count"])
    received = sum(row["received_order_count"] for row in delivery_rows)
    on_time = sum(row["on_time_order_count"] for row in delivery_rows)
    return {
        "context": {
            **params,
            "period_end_is_exclusive": True,
            "dataset_order_count": len(dataset["orders"]),
            "currency": "USD",
            "source": "Independent portfolio demonstration with public business names and fictional operational records",
            "data_notice": DATA_NOTICE,
            "attribution_scope": "The public names are illustrative labels, not actual client financial impact or evidence that Ziana Bennett worked with each business.",
            "business_context_document": "../docs/business-context.md",
        },
        "supplier_order_value": {
            "rows": value_rows,
            "total_order_count": sum(row["order_count"] for row in value_rows),
            "total_order_value_cents": sum(row["order_value_cents"] for row in value_rows),
        },
        "overdue_orders": {
            "rows": overdue_rows,
            "total_order_count": len(overdue_rows),
            "total_order_value_cents": sum(row["order_value_cents"] for row in overdue_rows),
        },
        "on_time_delivery": {
            "rows": delivery_rows,
            "received_order_count": received,
            "on_time_order_count": on_time,
            "on_time_rate_pct": percentage(on_time, received),
        },
    }


def svg_chart(title, subtitle, bars, unit, maximum=None):
    """Render exact computed values as a self-contained accessible SVG."""
    width = 960
    height = 204 + max(1, len(bars)) * 64
    left = 280
    plot_width = 500
    maximum = maximum if maximum is not None else max([bar[1] for bar in bars] + [1])
    description = "; ".join(f"{label}: {display}" for label, value, display in bars) or "No eligible orders"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}</title>',
        f'<desc id="desc">{html.escape(DATA_NOTICE + " " + description)}</desc>',
        '<rect width="100%" height="100%" rx="16" fill="#f6f8fb"/>',
        f'<text x="32" y="42" fill="#142b42" font-family="Arial, sans-serif" font-size="24" font-weight="700">{html.escape(title)}</text>',
        f'<text x="32" y="70" fill="#526479" font-family="Arial, sans-serif" font-size="14">{html.escape(subtitle)}</text>',
        f'<text x="32" y="96" fill="#233b51" font-family="Arial, sans-serif" font-size="14" font-weight="700">{html.escape(DATA_NOTICE)}</text>',
    ]
    for index, (label, value, display) in enumerate(bars):
        y = 130 + index * 64
        bar_width = round(plot_width * value / maximum, 2) if maximum else 0
        parts.extend([
            f'<text x="32" y="{y+25}" fill="#233b51" font-family="Arial, sans-serif" font-size="15">{html.escape(label)}</text>',
            f'<rect x="{left}" y="{y}" width="{plot_width}" height="38" rx="6" fill="#e3eaf1"/>',
            f'<rect x="{left}" y="{y}" width="{bar_width}" height="38" rx="6" fill="#1d7487"/>',
            f'<text x="{left+plot_width+18}" y="{y+25}" fill="#142b42" font-family="Arial, sans-serif" font-size="15" font-weight="700">{html.escape(display)}</text>',
        ])
    if not bars:
        parts.append('<text x="32" y="159" fill="#526479" font-family="Arial, sans-serif" font-size="16">No eligible orders for this report.</text>')
    parts.append(f'<text x="32" y="{height-22}" fill="#526479" font-family="Arial, sans-serif" font-size="12">{html.escape(unit)} · Fictional portfolio data</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render_summary(results):
    context = results["context"]
    values = results["supplier_order_value"]
    overdue = results["overdue_orders"]
    delivery = results["on_time_delivery"]
    rate = "Unavailable" if delivery["on_time_rate_pct"] is None else f'{delivery["on_time_rate_pct"]:.2f}%'
    lines = [
        "# Reporting results", "", "[Project overview](../README.md) · [Machine-readable results](report_results.json)", "",
        f"**{DATA_NOTICE}** These figures do not describe the named businesses' actual finances or delivery performance. [Read the business context and source distinctions](../docs/business-context.md).", "",
        f"Period **{context['period_start']} to {context['period_end']}**, with the end date excluded. Snapshot **{context['as_of']}**. The complete fixture contains **{context['dataset_order_count']} fictional orders**.", "",
        "## Measures", "",
        "| Measure | Computed result |", "| --- | ---: |",
        f"| Qualifying purchase orders | {values['total_order_count']} |",
        f"| Qualifying purchase order value | {money(values['total_order_value_cents'])} |",
        f"| Open overdue orders at the snapshot | {overdue['total_order_count']} |",
        f"| Value of open overdue orders | {money(overdue['total_order_value_cents'])} |",
        f"| Received orders in the period | {delivery['received_order_count']} |",
        f"| Received on time | {delivery['on_time_order_count']} |",
        f"| On-time delivery rate | {rate} |", "",
        "The order-value measure uses booking date. The delivery measure uses receipt date. The overdue report uses the snapshot date and includes older open orders, regardless of the selected reporting month.", "",
        "## Fictional purchase order value by named example", "",
        "![Fictional purchase order value by named business example](supplier_order_value.svg)", "",
        "| Named business example | Fictional orders | Fictional order value |", "| --- | ---: | ---: |",
    ]
    for row in values["rows"]:
        lines.append(f"| {row['supplier_label']} | {row['order_count']} | {money(row['order_value_cents'])} |")
    if not values["rows"]:
        lines.append("| No qualifying orders | 0 | $0.00 |")
    lines.extend(["", "## Fictional open overdue orders", "", "| Fictional order | Named business example | Fictional promised date | Days overdue | Fictional order value |", "| --- | --- | --- | ---: | ---: |"])
    for row in overdue["rows"]:
        lines.append(f"| {row['order_id']} | {row['supplier_label']} | {row['promised_date']} | {row['days_overdue']} | {money(row['order_value_cents'])} |")
    if not overdue["rows"]:
        lines.append("| No overdue orders | — | — | — | $0.00 |")
    lines.extend(["", "## Fictional on-time delivery", "", "![Fictional on-time delivery by named business example](delivery_performance.svg)", "", "| Named business example | Fictional receipts | Fictional on-time receipts | Fictional rate |", "| --- | ---: | ---: | ---: |"])
    for row in delivery["rows"]:
        lines.append(f"| {row['supplier_label']} | {row['received_order_count']} | {row['on_time_order_count']} | {row['on_time_rate_pct']:.2f}% |")
    if not delivery["rows"]:
        lines.append("| No eligible receipts | 0 | 0 | Unavailable |")
    lines.extend(["", "The overall rate is calculated from all eligible orders. It is not an average of supplier percentages. Suppliers with no receipts have no delivery rate and are omitted from that chart.", "", "## Reading the output", "", "These measures verify the behavior of a fictional reporting model. The named examples give the demonstration public business context; their amounts, rankings, overdue orders and delivery rates have no real-world performance meaning. They do not establish actual client financial impact or work Ziana Bennett performed for each business. In a real report, the value ranking and overdue list would guide investigation using validated operational data.", "", "Regenerate this folder with `python3 run.py`. Its JSON, tables, and charts are produced from the same report objects.", ""])
    return "\n".join(lines)


def write_outputs(results, output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "report_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (output_directory / "summary.md").write_text(render_summary(results), encoding="utf-8")
    context = results["context"]
    subtitle = f"{context['period_start']} to {context['period_end']} exclusive · Snapshot {context['as_of']}"
    value_bars = [(row["supplier_label"], row["order_value_cents"], money(row["order_value_cents"])) for row in results["supplier_order_value"]["rows"]]
    delivery_bars = [(row["supplier_label"], row["on_time_rate_pct"], f"{row['on_time_rate_pct']:.2f}%") for row in results["on_time_delivery"]["rows"]]
    (output_directory / "supplier_order_value.svg").write_text(svg_chart("Fictional purchase order value by named example", subtitle, value_bars, "USD · Integer cents used in calculations"), encoding="utf-8")
    (output_directory / "delivery_performance.svg").write_text(svg_chart("Fictional on-time delivery by named example", subtitle, delivery_bars, "Percentage of eligible received orders · Scale 0 to 100%", maximum=100), encoding="utf-8")

