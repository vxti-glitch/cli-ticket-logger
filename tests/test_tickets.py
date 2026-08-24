import argparse
import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import tickets


class TicketCommandTests(unittest.TestCase):
    def test_new_and_resolve_noninteractive(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "tickets.json"

            tickets.cmd_new(
                argparse.Namespace(
                    db=db,
                    description="VPN client fails with error 800",
                    category="Network / Connectivity",
                    priority="High",
                )
            )
            data = tickets.load_db(db)
            self.assertEqual(data["next_id"], 1002)
            self.assertEqual(data["tickets"][0]["status"], "open")

            tickets.cmd_resolve(
                argparse.Namespace(
                    db=db,
                    id=1001,
                    notes="Updated VPN client and restarted service",
                )
            )
            data = tickets.load_db(db)
            self.assertEqual(data["tickets"][0]["status"], "resolved")
            self.assertIn("Updated VPN", data["tickets"][0]["resolution_notes"])

    def test_export_uses_requested_output_path(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "tickets.json"
            output = Path(tmp) / "export.csv"
            tickets.save_db(
                {
                    "next_id": 1002,
                    "tickets": [
                        {
                            "id": 1001,
                            "status": "open",
                            "category": "Hardware",
                            "priority": "Low",
                            "description": "Mouse replacement",
                            "resolution_notes": "",
                            "opened": "2026-08-23 12:00:00",
                            "resolved": "",
                        }
                    ],
                },
                db,
            )

            tickets.cmd_export(argparse.Namespace(db=db, output=output))

            with output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["id"], "1001")


if __name__ == "__main__":
    unittest.main()
