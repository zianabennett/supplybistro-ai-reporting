"""Rebuild the fictional fixture. No random seed, network, or current date used."""

import json
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def generate_dataset():
    suppliers = [
        {"supplier_id": "SUP-A", "supplier_label": "Supplier Alpha"},
        {"supplier_id": "SUP-B", "supplier_label": "Supplier Beta"},
        {"supplier_id": "SUP-C", "supplier_label": "Supplier Gamma"},
        {"supplier_id": "SUP-D", "supplier_label": "Supplier Delta"},
    ]
    orders = []
    base = date(2026, 8, 25)
    for number in range(1, 61):
        ordered = base + timedelta(days=((number - 1) * 3) % 43)
        promised = ordered + timedelta(days=4 + number % 7)
        route = number % 6
        received = None
        cancelled = None
        if route == 0:
            cancelled = ordered + timedelta(days=2)
        elif route == 2:
            received = promised
        elif route == 3:
            received = promised - timedelta(days=2)
        elif route == 4:
            received = promised + timedelta(days=3)
        elif route == 5:
            received = promised - timedelta(days=1)
        orders.append({
            "order_id": f"PO{number:03d}",
            "supplier_id": suppliers[(number - 1) % 4]["supplier_id"],
            "order_date": ordered.isoformat(),
            "promised_date": promised.isoformat(),
            "received_date": received.isoformat() if received else None,
            "cancelled_date": cancelled.isoformat() if cancelled else None,
            "order_value_cents": 50000 + (number * 7919) % 450000,
            "currency": "USD",
        })

    # Explicit fixtures make the important business boundaries easy to audit.
    edges = [
        ("PO061", "SUP-A", "2026-08-31", "2026-09-05", "2026-09-05", None, 120000),
        ("PO062", "SUP-B", "2026-09-01", "2026-09-05", "2026-09-05", None, 150000),
        ("PO063", "SUP-C", "2026-09-30", "2026-10-05", "2026-10-05", None, 260000),
        ("PO064", "SUP-D", "2026-10-01", "2026-10-06", None, None, 340000),
        ("PO065", "SUP-A", "2026-09-15", "2026-09-30", None, None, 180000),
        ("PO066", "SUP-B", "2026-09-16", "2026-09-29", None, None, 220000),
        ("PO067", "SUP-C", "2026-09-10", "2026-09-20", None, "2026-09-12", 90000),
        ("PO068", "SUP-D", "2026-09-05", "2026-09-15", "2026-09-15", None, 125000),
        ("PO069", "SUP-A", "2026-09-06", "2026-09-15", "2026-09-14", None, 175000),
        ("PO070", "SUP-B", "2026-09-07", "2026-09-15", "2026-09-17", None, 155000),
        ("PO071", "SUP-C", "2026-09-03", "2026-09-20", None, "2026-10-02", 240000),
        ("PO072", "SUP-D", "2026-09-19", "2026-10-02", "2026-10-02", None, 285000),
    ]
    for order_id, supplier_id, ordered, promised, received, cancelled, cents in edges:
        orders.append({
            "order_id": order_id,
            "supplier_id": supplier_id,
            "order_date": ordered,
            "promised_date": promised,
            "received_date": received,
            "cancelled_date": cancelled,
            "order_value_cents": cents,
            "currency": "USD",
        })
    return {
        "metadata": {
            "dataset": "Fictional purchase orders for a portfolio reporting exercise",
            "version": 1,
            "provenance": "Independent AI-assisted portfolio extension; no employer data",
            "generation": "Deterministic arithmetic fixture plus twelve explicit boundary cases",
            "grain": "One row per purchase order",
            "default_period_start": "2026-09-01",
            "default_period_end_exclusive": "2026-10-01",
            "default_as_of": "2026-09-30",
        },
        "suppliers": suppliers,
        "orders": orders,
    }


if __name__ == "__main__":
    target = ROOT / "data" / "synthetic_purchase_orders.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(generate_dataset(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote 72 fictional orders to {target.relative_to(ROOT)}")

