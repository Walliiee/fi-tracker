#!/usr/bin/env python3
"""
Seed data for fi-tracker demo.
Run: python seed.py
"""
import db

def seed_all():
    conn = db.get_db()
    
    # Seed fundraising entries
    fundraising = [
        ("DIF Lokale og Anlægsfond", 150000, 150000, "received", "2026-03-01", "Godkendt til hal renovering"),
        ("DGI Lokale Aktivitetspulje", 75000, 0, "applied", "2026-04-15", "Afventer svar"),
        ("Odense Kommune Idrætspulje", 50000, 0, "identified", "2026-05-01", "Skal ansøges snart"),
    ]
    conn.executemany(
        '''INSERT INTO fundraising (name, amount_applied, amount_received, status, deadline, notes)
           VALUES (?, ?, ?, ?, ?, ?)''', fundraising
    )
    
    # Seed tasks
    tasks = [
        ("Bestil nye bolde til sommersæson", "Lars", "todo", "medium", "2026-05-15", "Kontakt Sportmaster"),
        ("Opdatere hjemmeside", "Mia", "started", "high", "2026-04-30", "Nye billeder fra sidste sæson"),
        ("Generalforsamling forberedelse", "Formand", "todo", "high", "2026-03-10", "Find lokale, send invitationer"),
        ("Facebook opslag - tilmelding", "Sofie", "done", "low", "2026-02-20", "Udsendt 18/2"),
        ("Ansøg Lokalepulje", "Lars", "started", "high", "2026-02-28", "Deadline nærmer sig!"),
    ]
    conn.executemany(
        '''INSERT INTO tasks (title, assignee, status, priority, due_date, notes)
           VALUES (?, ?, ?, ?, ?, ?)''', tasks
    )
    
    # Seed ideas
    ideas = [
        ("Familie weekend-event", "Overnatning på skolen + aktiviteter", "aktivitet", "new", 3, "weekend, familie, event"),
        ("Sponsoraftale med lokal bager", "Tilbyde reklameplads på hjemmeside", "samarbejde", "discussed", 2, "sponsor, økonomi"),
        ("Nyt træningsudstyr", "Køb flere måtter og kegler", "udstyr", "new", -1, "indkøb, træning"),
        ("Samarbejde med naboforening", "Fælles event i sommerferien", "samarbejde", "approved", 5, "samarbejde, sommer, event"),
    ]
    conn.executemany(
        '''INSERT INTO ideas (title, description, category, status, vote_score, tags)
           VALUES (?, ?, ?, ?, ?, ?)''', ideas
    )
    
    # Seed content posts
    posts = [
        ("Vinterferie aktiviteter", "facebook", "2026-02-15", "posted", None, "Sofie", "https://facebook.com/...", "Få likes på dette opslag"),
        ("Tilmelding til forårssæson", "multiple", "2026-02-25", "scheduled", 1, None, None, "Husk at linke til tilmelding"),
        ("Ny træner præsentation", "instagram", "2026-03-01", "draft", None, None, None, "Tag billeder med Mia"),
    ]
    conn.executemany(
        '''INSERT INTO content_posts (title, platform, planned_date, status, event_id, posted_by, link, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', posts
    )
    
    # Note: events are already seeded in db.py _seed_events()
    
    conn.commit()
    conn.close()
    print("✅ Seed data added successfully!")

if __name__ == "__main__":
    seed_all()
