import sqlite3
import json
import os
import logging

DATABASE = os.environ.get('DATABASE_URL', os.path.join(os.path.dirname(__file__), 'data', 'fi_tracker.db'))

MIGRATIONS = [
    ('001', 'events: add needs_comms column',
     'ALTER TABLE events ADD COLUMN needs_comms INTEGER DEFAULT 0'),
    ('002', 'ideas: add vote_score column',
     'ALTER TABLE ideas ADD COLUMN vote_score INTEGER DEFAULT 0'),
    ('003', 'ideas: add tags column',
     'ALTER TABLE ideas ADD COLUMN tags TEXT DEFAULT ""'),
    ('004', 'fundraising: add description column',
     'ALTER TABLE fundraising ADD COLUMN description TEXT'),
    ('005', 'fundraising: add budget column',
     'ALTER TABLE fundraising ADD COLUMN budget TEXT DEFAULT "{}"'),
    ('006', 'users: create table',
     '''CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          name TEXT NOT NULL,
          password_hash TEXT NOT NULL,
          role TEXT DEFAULT "user",
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    conn = get_db()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    _run_migrations(conn)
    _migrate_pipeline_to_fundraising(conn)
    _seed_events(conn)
    conn.close()


def _run_migrations(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    applied = {r['version'
] for r in conn.execute(
        'SELECT version FROM schema_migrations'
    ).fetchall()}

    for version, description, sql in MIGRATIONS:
        if version in applied:
            continue
        try:
            conn.execute(sql)
            conn.execute(
                'INSERT INTO schema_migrations (version, description) VALUES (?, ?)',
                (version, description)
            )
            conn.commit()
            logging.info('Migration %s applied: %s', version, description)
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                conn.execute(
                    'INSERT OR IGNORE INTO schema_migrations (version, description) VALUES (?, ?)',
                    (version, description)
                )
                conn.commit()
                logging.info('Migration %s skipped (already present): %s', version, description)
            else:
                raise


def _migrate_pipeline_to_fundraising(conn):
    pipeline = conn.execute('SELECT * FROM fund_pipeline').fetchall()
    if not pipeline:
        return
    existing_names = {r['name'
] for r in conn.execute(
        "SELECT name FROM fundraising WHERE status='research'"
    ).fetchall()}
    to_migrate = [r for r in pipeline if r['fund_name'
] not in existing_names]
    if not to_migrate:
        return
    for row in to_migrate:
        conn.execute(
            '''INSERT INTO fundraising (name, description, amount_applied, amount_received, status, deadline, budget, notes)
               VALUES (?, ?, ?, 0, 'research', ?, '{}', ?)''',
            (row['fund_name'
], row['description'], row['amount_estimate'] or 0, row['deadline'], row['notes'])
        )
    conn.commit()
    logging.info('Migrated %d fund_pipeline entries to fundraising', len(to_migrate))


def _seed_events(conn):
    count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0
]
    if count > 0:
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
