# CLI Ticket Logger

[github.com/vxti-glitch](https://github.com/vxti-glitch)

A command-line IT support ticket tracker. Log issues, set priority and category, mark tickets resolved with notes, and export your ticket history to CSV. No external dependencies — pure Python.

Built to demonstrate understanding of what a support ticket actually contains and how resolution workflows are structured.

---

## Commands

```bash
python tickets.py new              # Create a new ticket (interactive)
python tickets.py list             # List all open tickets
python tickets.py list --all       # List all tickets including resolved
python tickets.py view 1001        # View full details of ticket #1001
python tickets.py resolve 1001     # Mark ticket #1001 as resolved
python tickets.py export           # Export all tickets to timestamped CSV
```

---

## Example session

```
$ python tickets.py new

============================================================
  NEW TICKET
============================================================

Describe the issue:
> User cannot connect to VPN — error 800, remote server not responding

Category:
  1. Hardware
  2. Software / Application
  3. Network / Connectivity
  4. Account / Access
  5. Printer / Peripheral
  6. Email
  7. Other
  Enter number: 3

Priority:
  1. Low
  2. Medium
  3. High
  4. Critical
  Enter number: 3

[✓] Ticket #1001 created — Network / Connectivity | High priority

---

$ python tickets.py list

============================================================
  OPEN TICKETS (1 total)
============================================================
  ID       Status       Priority   Category                     Opened
  ────────────────────────────────────────────────────────────
  🔴 #1001  open         High       Network / Connectivity       2026-08-03 20:15:00

---

$ python tickets.py resolve 1001

============================================================
  RESOLVE TICKET #1001
============================================================
  Issue: User cannot connect to VPN — error 800, remote server not...

Resolution notes (what fixed it?):
> Confirmed VPN client was outdated — updated to v5.2, restarted service, connection restored.

[✓] Ticket #1001 marked as resolved.
```

---

## Data storage

Tickets are stored locally in `tickets.json` — human-readable and portable. Export to CSV for spreadsheet-based reporting or to simulate attaching to a formal ticketing system.

**CSV export columns:** ID, Status, Category, Priority, Description, Resolution Notes, Opened, Resolved

---

## Help Desk relevance

Every professional ticketing system (Zendesk, Freshdesk, ServiceNow, Jira Service Management) is built on the same data model this tool implements: a unique ID, a category, a priority level, a description, resolution notes, and timestamps. Building this from scratch demonstrates that the underlying structure of a ticket isn't a mystery — it's something I understand well enough to implement.

**Skills:** Python · CLI tool design · JSON data persistence · CSV export · Ticketing system concepts

---

*Part of the [vxti-glitch IT Support Portfolio](https://github.com/vxti-glitch)*
