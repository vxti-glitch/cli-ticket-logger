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
import sys

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.json")


def load_db():
    if not os.path.isfile(DB_FILE):
        return {"next_id": 1001, "tickets": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


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
    db = load_db()
    ticket_id = db["next_id"]

    print("\n" + separator("="))
    print("  NEW TICKET")
    print(separator("="))

    description = input("\nDescribe the issue:\n> ").strip()
    if not description:
        print("[ERROR] Description cannot be empty.")
        sys.exit(1)

    category = prompt_choice("Category:", CATEGORIES)
    priority = prompt_choice("Priority:", PRIORITIES)

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
    save_db(db)

    print(f"\n[✓] Ticket #{ticket_id} created — {category} | {priority} priority")


def cmd_list(args):
    db = load_db()
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
        status_icon = "✅" if t["status"] == "resolved" else "🔴"
        print(
            f"  {status_icon} #{t['id']:<5} {t['status']:<12} {t['priority']:<10} "
            f"{t['category']:<28} {t['opened']}"
        )
    print(separator())


def cmd_view(args):
    db = load_db()
    matches = [t for t in db["tickets"] if t["id"] == args.id]
    if not matches:
        print(f"[ERROR] Ticket #{args.id} not found.")
        sys.exit(1)
    print(format_ticket(matches[0]))


def cmd_resolve(args):
    db = load_db()
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
    notes = input("\nResolution notes (what fixed it?):\n> ").strip()
    if not notes:
        print("[ERROR] Resolution notes cannot be empty.")
        sys.exit(1)

    ticket["status"] = "resolved"
    ticket["resolution_notes"] = notes
    ticket["resolved"] = now_str()
    save_db(db)
    print(f"\n[✓] Ticket #{args.id} marked as resolved.")


def cmd_export(args):
    db = load_db()
    if not db["tickets"]:
        print("[INFO] No tickets to export.")
        return

    export_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"tickets_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    fields = ["id", "status", "category", "priority", "description",
              "resolution_notes", "opened", "resolved"]

    with open(export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(db["tickets"])

    print(f"[✓] Exported {len(db['tickets'])} ticket(s) to: {export_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CLI Ticket Logger — command-line IT support ticket tracker."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("new",     help="Create a new ticket")

    p_list = sub.add_parser("list",  help="List tickets")
    p_list.add_argument("--all", action="store_true",
                        help="Include resolved tickets")

    p_view = sub.add_parser("view",   help="View a ticket by ID")
    p_view.add_argument("id", type=int, help="Ticket ID (e.g. 1001)")

    p_res = sub.add_parser("resolve", help="Mark a ticket as resolved")
    p_res.add_argument("id", type=int, help="Ticket ID (e.g. 1001)")

    sub.add_parser("export",  help="Export all tickets to CSV")

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
