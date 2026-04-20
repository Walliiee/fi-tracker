# fi-tracker

Familieidræt organisation tracker. Local-first, dark-themed, no cloud required.

## Features

- Dashboard with live summary cards and AI-powered org reports
- Fundraising pipeline (kanban) with win rate tracking
- Fund pipeline with deadline urgency indicators
- Tasks with assignee, overdue highlighting, and status workflow
- Ideas with voting, tags, and approve-to-task workflow
- Årshjul — 12-month Danish sports org calendar (DIF/DGI deadlines, hal-tider, governance)
- Communications — content calendar + post log linked to årshjul events
- CSV export for all modules
- Print-ready reports

## Stack

Python 3 · Flask · SQLite · Plain HTML/JS · Dark theme · Ollama (optional, for AI reports)

## Quick Start

```bash
pip install flask
python app.py
# Open http://localhost:5002
```

## Seed Data

To populate the database with demo data:

```bash
python seed.py
```

## Ports

- fi-tracker: 5002

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| N | New item in current tab |
| Esc | Close modal |
| 1–7 | Switch tabs |

## GitHub

https://github.com/Walliiee/fi-tracker
