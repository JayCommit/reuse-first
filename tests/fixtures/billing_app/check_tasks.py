"""Task acceptance checks, separate from the indexer's automated tests."""

import csv
import io
import unittest

from client import BillingClient
from commands import account_total, invoice_ids
from exports import export_invoice_csv
from presentation import render_total
from views import render_invoice, render_receipt


class ClientTask(unittest.TestCase):
    def test_invoice_ids_and_existing_caller(self):
        class Transport:
            def __init__(self):
                self.calls = []

            def get(self, path, **params):
                self.calls.append((path, params))
                if params["cursor"] is None:
                    return {"items": [{"id": "i1", "cents": 100}], "next": "page2"}
                return {"items": [{"id": "i2", "cents": 200}]}

        transport = Transport()
        client = BillingClient(transport)
        self.assertEqual(invoice_ids(client, "a1"), ["i1", "i2"])
        self.assertEqual([params["cursor"] for _, params in transport.calls], [None, "page2"])
        self.assertTrue(all(path == "/invoices" and p["account"] == "a1"
                            for path, p in transport.calls))
        self.assertEqual(account_total(client, "a1"), 300)

    def test_empty_and_error(self):
        class Empty:
            def iter_invoices(self, account):
                return iter([])

        class Failed:
            def iter_invoices(self, account):
                raise ValueError("unavailable")

        self.assertEqual(invoice_ids(Empty(), "a1"), [])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            invoice_ids(Failed(), "a1")


class AmbiguousTask(unittest.TestCase):
    def test_invoice_format_and_existing_callers(self):
        row = {"id": "i1", "cents": -123456}
        self.assertEqual(render_invoice(row), "Invoice i1: -£1,234.56")
        self.assertEqual(render_receipt(row), "Receipt i1: -£1,234.56")
        self.assertEqual(render_total(0), "Total: £0.00")


class MissingTask(unittest.TestCase):
    def test_csv_round_trip_and_empty(self):
        rows = [{"id": 'i,"one"\nsecond', "cents": -5}]
        result = export_invoice_csv(rows)
        self.assertEqual(list(csv.reader(io.StringIO(result))),
                         [["id", "cents"], ['i,"one"\nsecond', "-5"]])
        self.assertEqual(list(csv.reader(io.StringIO(export_invoice_csv([])))),
                         [["id", "cents"]])


if __name__ == "__main__":
    unittest.main()
