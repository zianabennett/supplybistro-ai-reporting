"""Run all three reports and write consistent JSON, Markdown, and SVG outputs."""

import argparse
import json
from pathlib import Path

from reporting import ROOT, build_reports, money, write_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-09-01", help="Inclusive period start, YYYY-MM-DD")
    parser.add_argument("--end", default="2026-10-01", help="Exclusive period end, YYYY-MM-DD")
    parser.add_argument("--as-of", default="2026-09-30", help="Inclusive event snapshot date, YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    dataset = json.loads((ROOT / "data" / "synthetic_purchase_orders.json").read_text(encoding="utf-8"))
    try:
        results = build_reports(dataset, args.start, args.end, args.as_of)
    except ValueError as exc:
        parser.error(str(exc))
    write_outputs(results, args.output_dir)
    values = results["supplier_order_value"]
    overdue = results["overdue_orders"]
    delivery = results["on_time_delivery"]
    print(f"Purchase orders: {values['total_order_count']} | {money(values['total_order_value_cents'])}")
    print(f"Open overdue: {overdue['total_order_count']} | {money(overdue['total_order_value_cents'])}")
    display_rate = "unavailable" if delivery["on_time_rate_pct"] is None else f"{delivery['on_time_rate_pct']:.2f}%"
    print(f"On-time delivery: {delivery['on_time_order_count']}/{delivery['received_order_count']} | {display_rate}")
    print(f"Outputs written to {args.output_dir}")


if __name__ == "__main__":
    main()
