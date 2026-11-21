"""Business-boundary checks using small examples with independently known answers."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from generate_data import generate_dataset
from reporting import ROOT, build_reports, validate_dataset, write_outputs


def order(order_id, supplier="SUP-A", ordered="2026-09-01", promised="2026-09-10",
          received=None, cancelled=None, cents=10000):
    return {
        "order_id": order_id,
        "supplier_id": supplier,
        "order_date": ordered,
        "promised_date": promised,
        "received_date": received,
        "cancelled_date": cancelled,
        "order_value_cents": cents,
        "currency": "USD",
    }


def fixture(orders):
    return {
        "suppliers": [
            {"supplier_id": "SUP-A", "supplier_label": "Supplier Alpha"},
            {"supplier_id": "SUP-B", "supplier_label": "Supplier Beta"},
        ],
        "orders": orders,
    }


class ReportingTests(unittest.TestCase):
    def test_booking_boundaries_and_exact_cent_reconciliation(self):
        data = fixture([
            order("A", cents=1),
            order("B", supplier="SUP-B", ordered="2026-09-30", promised="2026-10-05", cents=2),
            order("C", ordered="2026-08-31", cents=800),
            order("D", ordered="2026-10-01", promised="2026-10-05", cents=900),
            order("E", cancelled="2026-09-02", cents=700),
        ])
        result = build_reports(data)["supplier_order_value"]
        self.assertEqual(result["total_order_count"], 2)
        self.assertEqual(result["total_order_value_cents"], 3)
        self.assertEqual(sum(row["order_value_cents"] for row in result["rows"]), 3)

    def test_later_cancellation_does_not_rewrite_earlier_snapshot(self):
        data = fixture([order("A", cancelled="2026-10-02", cents=12345)])
        earlier = build_reports(data)
        later = build_reports(data, as_of="2026-10-03")
        self.assertEqual(earlier["supplier_order_value"]["total_order_value_cents"], 12345)
        self.assertEqual(earlier["overdue_orders"]["total_order_count"], 1)
        self.assertEqual(later["supplier_order_value"]["total_order_count"], 0)
        self.assertEqual(later["overdue_orders"]["total_order_count"], 0)

    def test_later_receipt_is_still_open_at_earlier_snapshot(self):
        data = fixture([order("A", promised="2026-09-29", received="2026-10-02")])
        earlier = build_reports(data)
        later = build_reports(data, as_of="2026-10-03")
        self.assertEqual(earlier["overdue_orders"]["rows"][0]["days_overdue"], 1)
        self.assertEqual(later["overdue_orders"]["total_order_count"], 0)

    def test_due_today_and_snapshot_events_are_not_overdue(self):
        data = fixture([
            order("DUE", promised="2026-09-30"),
            order("RECEIVED", promised="2026-09-29", received="2026-09-30"),
            order("CANCELLED", promised="2026-09-29", cancelled="2026-09-30"),
            order("OLD", ordered="2026-08-01", promised="2026-08-10"),
            order("FUTURE", ordered="2026-10-01", promised="2026-10-01"),
        ])
        result = build_reports(data)["overdue_orders"]
        self.assertEqual([row["order_id"] for row in result["rows"]], ["OLD"])
        self.assertEqual(result["rows"][0]["days_overdue"], 51)

    def test_delivery_period_uses_receipt_date_and_treats_equality_as_on_time(self):
        data = fixture([
            order("A", ordered="2026-08-25", promised="2026-09-01", received="2026-09-01"),
            order("B", promised="2026-09-15", received="2026-09-14"),
            order("C", promised="2026-09-15", received="2026-09-16"),
            order("D", promised="2026-09-30", received="2026-10-01"),
            order("E"),
        ])
        result = build_reports(data)["on_time_delivery"]
        self.assertEqual(result["received_order_count"], 3)
        self.assertEqual(result["on_time_order_count"], 2)
        self.assertEqual(result["on_time_rate_pct"], 66.67)

    def test_delivery_rate_weights_orders_not_supplier_percentages(self):
        data = fixture([
            order("A", received="2026-09-10"),
            order("B", supplier="SUP-B", received="2026-09-11"),
            order("C", supplier="SUP-B", received="2026-09-12"),
            order("D", supplier="SUP-B", received="2026-09-13"),
        ])
        result = build_reports(data)["on_time_delivery"]
        self.assertEqual([row["on_time_rate_pct"] for row in result["rows"]], [100.0, 0.0])
        self.assertEqual(result["on_time_rate_pct"], 25.0)

    def test_no_receipts_has_an_unavailable_rate(self):
        result = build_reports(fixture([order("A")]))["on_time_delivery"]
        self.assertEqual(result["received_order_count"], 0)
        self.assertEqual(result["on_time_order_count"], 0)
        self.assertIsNone(result["on_time_rate_pct"])

    def test_as_of_date_prevents_future_receipts_and_bookings(self):
        data = fixture([
            order("A", received="2026-09-25"),
            order("B", ordered="2026-09-25", promised="2026-09-28"),
        ])
        result = build_reports(data, as_of="2026-09-20")
        self.assertEqual(result["supplier_order_value"]["total_order_count"], 1)
        self.assertEqual(result["on_time_delivery"]["received_order_count"], 0)

    def test_rejects_duplicate_ids_and_ambiguous_lifecycles(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_dataset(fixture([order("A"), order("A")]))
        with self.assertRaisesRegex(ValueError, "both received and cancelled"):
            validate_dataset(fixture([order("A", received="2026-09-10", cancelled="2026-09-11")]))

    def test_rejects_invalid_dates_and_monetary_units(self):
        for updates in (
            {"order_date": "2026-09-31"},
            {"promised_date": "2026-08-01"},
            {"received_date": "2026-08-31"},
            {"order_value_cents": 12.5},
            {"order_value_cents": -1},
            {"currency": "EUR"},
        ):
            with self.subTest(updates=updates):
                record = order("A")
                record.update(updates)
                with self.assertRaises(ValueError):
                    validate_dataset(fixture([record]))

    def test_rejects_unknown_suppliers_and_invalid_report_periods(self):
        with self.assertRaisesRegex(ValueError, "unknown supplier"):
            validate_dataset(fixture([order("A", supplier="MISSING")]))
        with self.assertRaisesRegex(ValueError, "later"):
            build_reports(fixture([]), period_start="2026-10-01", period_end="2026-09-01")

    def test_committed_fixture_matches_deterministic_generator(self):
        committed = json.loads((ROOT / "data" / "synthetic_purchase_orders.json").read_text(encoding="utf-8"))
        self.assertEqual(committed, generate_dataset())
        self.assertEqual(len(committed["orders"]), 72)
        validate_dataset(committed)

    def test_outputs_are_deterministic_and_retain_computed_values(self):
        report = build_reports(fixture([order("A", cents=12345, received="2026-09-10")]))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_outputs(report, output)
            first = {path.name: path.read_bytes() for path in output.iterdir()}
            write_outputs(copy.deepcopy(report), output)
            second = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(first, second)
            stored = json.loads(first["report_results.json"])
            self.assertEqual(stored["supplier_order_value"]["total_order_value_cents"], 12345)
            self.assertIn("$123.45", first["summary.md"].decode())


if __name__ == "__main__":
    unittest.main()
