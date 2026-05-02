import sqlite3
import json
import os

DATABASE = os.environ.get('DATABASE_URL', os.path.join(os.path.dirname(__file__), 'data', 'fi_tracker.db'))

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    conn = get_db()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.close()
    _migrate()
    _seed_events()

def _migrate():
    conn = get_db()
    _add_column(conn, 'ALTER TABLE events ADD COLUMN needs_comms INTEGER DEFAULT 0')
    _add_column(conn, 'ALTER TABLE ideas ADD COLUMN vote_score INTEGER DEFAULT 0')
    _add_column(conn, 'ALTER TABLE ideas ADD COLUMN tags TEXT DEFAULT ""')
    _add_column(conn, 'ALTER TABLE fundraising ADD COLUMN description TEXT')
    _add_column(conn, 'ALTER TABLE fundraising ADD COLUMN budget TEXT DEFAULT "{}"')
    conn.commit()
    # Migrate fund_pipeline entries to fundraising as status='research'
    _migrate_pipeline_to_fundraising(conn)
    conn.close()

def _migrate_pipeline_to_fundraising(conn):
    migrated = conn.execute("SELECT COUNT(*) FROM fundraising WHERE status='research'").fetchone()[0]
    if migrated > 0:
        return
    pipeline = conn.execute('SELECT * FROM fund_pipeline').fetchall()
    for row in pipeline:
        conn.execute(
            '''INSERT INTO fundraising (name, description, amount_applied, amount_received, status, deadline, budget, notes)
               VALUES (?, ?, ?, 0, 'research', ?, '{}', ?)''',
            (row['fund_name'], row['description'], row['amount_estimate'] or 0, row['deadline'], row['notes'])
        )
    if pipeline:
        conn.commit()

def _add_column(conn, sql):
    try:
        conn.execute(sql)
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

def _seed_events():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    if count > 0:
        conn.close()
        return
    seed_events = [
        ("Generalforsamling", "2026-03-15", None, "board", "Yearly AGM", "yearly", 0),
        ("Ansøg kommunalt tilskud", "2026-02-01", None, "grant_deadline", "Yearly kommune support application", "yearly", 1),
        ("Ansøg hal-tider", "2026-08-15", None, "facility", "Apply for hall time next season", "yearly", 1),
        ("Årsregnskab indsendes", "2026-04-30", None, "reporting", "Submit yearly financial report", "yearly", 0),
        ("Sæsonstart", "2026-09-01", None, "season", "Season begins", "yearly", 0),
        ("Sæsonslut", "2026-06-15", None, "season", "Season ends", "yearly", 0),
        ("Medlemsfornyelse", "2026-08-01", "2026-09-30", "membership", "Annual membership renewal period", "yearly", 1),
        ("DIF ansøgningsfrist", "2026-03-01", None, "grant_deadline", "DIF development fund deadline", "yearly", 1),
        ("DGI ansøgningsfrist", "2026-04-15", None, "grant_deadline", "DGI local activity fund deadline", "yearly", 1),
    ]
    for e in seed_events:
        conn.execute(
            '''INSERT INTO events (title, event_date, end_date, category, description, recurring, needs_comms)
               VALUES (?, ?, ?, ?, ?, ?, ?)''', e
        )
    conn.commit()
    conn.close()
