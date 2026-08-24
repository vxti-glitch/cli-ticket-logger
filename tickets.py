"""
cli-ticket-logger
------------------
A command-line IT ticketing tool for logging, tracking, and resolving
support tickets locally. Tickets are stored in a JSON file and can be
exported to CSV for reporting.

Commands:
    python tickets.py new          Create a new ticket
    python tickets.py list         List all open tickets
    python tickets.py list --all   List all tickets (open + resolved)
    python tickets.py view  <id>   View full details of a ticket
    python tickets.py resolve <id> Mark a ticket as resolved
    python tickets.py export       Export all tickets to tickets_export.csv

No external libraries required — pure Python stdlib.
"""

import argparse
import csv
import datetime
import json
import os
import tempfile
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

DEFAULT_DB_FILE = Path(__file__).with_name("tickets.json")


def load_db(db_file=DEFAULT_DB_FILE):
    db_path = Path(db_file)
    if not db_path.is_file():
        return {"next_id": 1001, "tickets": []}
    try:
        with db_path.open("r", encoding="utf-8") as f:
            db = json.load(f)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[ERROR] Ticket database is invalid JSON: {db_path} ({exc})") from exc

    if not isinstance(db, dict) or "next_id" not in db or "tickets" not in db:
        raise SystemExit(f"[ERROR] Ticket database has an unsupported schema: {db_path}")
    return db


def save_db(db, db_file=DEFAULT_DB_FILE):
    db_path = Path(db_file)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(db_path.parent),
        delete=False,
    ) as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
        f.write("\n")
        temp_name = f.name

    os.replace(temp_name, db_path)


# ---------------------------------------------------------------------------
# Ticket helpers
# ---------------------------------------------------------------------------

CATEGORIES = [
    "Hardware",
    "Software / Application",
    "Network / Connectivity",
    "Account / Access",
    "Printer / Peripheral",
    "Email",
    "Other",
]

PRIORITIES = ["Low", "Medium", "High", "Critical"]


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def prompt_choice(prompt, options):
    """Display a numbered menu and return the chosen value."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  Please enter a number between 1 and {len(options)}.")


def separator(char="─", width=60):
    return char * width


def format_ticket(t, short=False):
    lines = [
        separator(),
        f"  Ticket #{t['id']}   [{t['status'].upper()}]   Priority: {t['priority']}",
        f"  Category : {t['category']}",
        f"  Opened   : {t['opened']}",
    ]
    if t.get("resolved"):
        lines.append(f"  Resolved : {t['resolved']}")
    if not short:
        lines += [
            separator("·"),
            f"  DESCRIPTION",
            f"  {t['description']}",
        ]
        if t.get("resolution_notes"):
            lines += [
                separator("·"),
                f"  RESOLUTION NOTES",
                f"  {t['resolution_notes']}",
            ]
    lines.append(separator())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_new(args):
    db = load_db(args.db)
    ticket_id = db["next_id"]

    print("\n" + separator("="))
    print("  NEW TICKET")
    print(separator("="))

    description = (args.description or "").strip()
    if not description:
        description = input("\nDescribe the issue:\n> ").strip()
    if not description:
        print("[ERROR] Description cannot be empty.")
        sys.exit(1)

    category = args.category or prompt_choice("Category:", CATEGORIES)
    priority = args.priority or prompt_choice("Priority:", PRIORITIES)

    ticket = {
        "id":               ticket_id,
        "status":           "open",
        "category":         category,
        "priority":         priority,
        "description":      description,
        "resolution_notes": "",
        "opened":           now_str(),
        "resolved":         "",
    }

    db["tickets"].append(ticket)
    db["next_id"] += 1
    save_db(db, args.db)

    print(f"\n[OK] Ticket #{ticket_id} created - {category} | {priority} priority")


def cmd_list(args):
    db = load_db(args.db)
    tickets = db["tickets"]

    if not args.all:
        tickets = [t for t in tickets if t["status"] == "open"]

    if not tickets:
        label = "tickets" if args.all else "open tickets"
        print(f"\n  No {label} found.")
        return

    label = "ALL TICKETS" if args.all else "OPEN TICKETS"
    print(f"\n{separator('=')}")
    print(f"  {label} ({len(tickets)} total)")
    print(separator("="))
    print(f"  {'ID':<8} {'Status':<12} {'Priority':<10} {'Category':<28} Opened")
    print(separator("─"))
    for t in tickets:
        status_icon = "[RESOLVED]" if t["status"] == "resolved" else "[OPEN]"
        print(
            f"  {status_icon} #{t['id']:<5} {t['status']:<12} {t['priority']:<10} "
            f"{t['category']:<28} {t['opened']}"
        )
    print(separator())


def cmd_view(args):
    db = load_db(args.db)
    matches = [t for t in db["tickets"] if t["id"] == args.id]
    if not matches:
        print(f"[ERROR] Ticket #{args.id} not found.")
        sys.exit(1)
    print(format_ticket(matches[0]))


def cmd_resolve(args):
    db = load_db(args.db)
    matches = [t for t in db["tickets"] if t["id"] == args.id]
    if not matches:
        print(f"[ERROR] Ticket #{args.id} not found.")
        sys.exit(1)

    ticket = matches[0]
    if ticket["status"] == "resolved":
        print(f"[INFO] Ticket #{args.id} is already resolved.")
        return

    print(f"\n{separator('=')}")
    print(f"  RESOLVE TICKET #{args.id}")
    print(separator("="))
    print(f"  Issue: {ticket['description'][:80]}...")
    notes = (args.notes or "").strip()
    if not notes:
        notes = input("\nResolution notes (what fixed it?):\n> ").strip()
    if not notes:
        print("[ERROR] Resolution notes cannot be empty.")
        sys.exit(1)

    ticket["status"] = "resolved"
    ticket["resolution_notes"] = notes
    ticket["resolved"] = now_str()
    save_db(db, args.db)
    print(f"\n[OK] Ticket #{args.id} marked as resolved.")


def cmd_export(args):
    db = load_db(args.db)
    if not db["tickets"]:
        print("[INFO] No tickets to export.")
        return

    export_path = Path(args.output) if args.output else Path(__file__).with_name(
        f"tickets_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    export_path.parent.mkdir(parents=True, exist_ok=True)

    fields = ["id", "status", "category", "priority", "description",
              "resolution_notes", "opened", "resolved"]

    with export_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(db["tickets"])

    print(f"[OK] Exported {len(db['tickets'])} ticket(s) to: {export_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CLI Ticket Logger — command-line IT support ticket tracker."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_FILE,
        help="Path to the ticket JSON database. Default: tickets.json next to this script.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new ticket")
    p_new.add_argument("--description", help="Ticket description for non-interactive use")
    p_new.add_argument("--category", choices=CATEGORIES, help="Ticket category")
    p_new.add_argument("--priority", choices=PRIORITIES, help="Ticket priority")

    p_list = sub.add_parser("list",  help="List tickets")
    p_list.add_argument("--all", action="store_true",
                        help="Include resolved tickets")

    p_view = sub.add_parser("view",   help="View a ticket by ID")
    p_view.add_argument("id", type=int, help="Ticket ID (e.g. 1001)")

    p_res = sub.add_parser("resolve", help="Mark a ticket as resolved")
    p_res.add_argument("id", type=int, help="Ticket ID (e.g. 1001)")
    p_res.add_argument("--notes", help="Resolution notes for non-interactive use")

    p_export = sub.add_parser("export", help="Export all tickets to CSV")
    p_export.add_argument("--output", type=Path, help="CSV export path")

    args = parser.parse_args()

    dispatch = {
        "new":     cmd_new,
        "list":    cmd_list,
        "view":    cmd_view,
        "resolve": cmd_resolve,
        "export":  cmd_export,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
