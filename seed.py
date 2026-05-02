#!/usr/bin/env python3
"""Seed data for fi-tracker demo. Run: python seed.py"""
import json
import db

def seed_all():
    conn = db.get_db()

    # Clear existing data
    conn.execute('DELETE FROM fundraising')
    conn.execute('DELETE FROM tasks')
    conn.execute('DELETE FROM ideas')
    conn.execute('DELETE FROM events')
    conn.execute('DELETE FROM content_posts')

    # Seed unified grants (fundraising)
    grants = [
        ("DIF Lokale og Anlægsfond",      "Hal renovering",                150000, 150000, "received",    "2026-03-01", json.dumps({"faciliteter":150000}),                                         "Godkendt til hal renovering"),
        ("DGI Lokale Aktivitetspulje",     "Lokale aktiviteter",            75000,  0,      "applied",     "2026-04-15", json.dumps({"udstyr":40000,"toj":10000,"rekruttering":25000}),              "Afventer svar"),
        ("Odense Kommune Idrætspulje",     "",                              34000,  0,      "identified",  "2026-05-20", json.dumps({"udstyr":25000,"pr":2000,"marketing":5000,"toj":2000}),         "Skal ansøges snart"),
        ("Nordea Fonden",                  "Nyt anlæg",                     200000, 0,      "applied",     "2026-06-01", json.dumps({"faciliteter":200000}),                                         "Stor ansøgning"),
        ("Lokale og Anlægsfonden",         "",                              80000,  0,      "rejected",    "2025-12-01", json.dumps({}),                                                              "Afvist — prøv igen næste år"),
        ("Kulturministeriet Idrætspulje",  "Støtte til bredde-idræt",       100000, 0,      "research",    "2026-07-01", json.dumps({}),                                                              "Researche krav"),
        ("TrygFonden Lokalsamfund",        "Fællesskabsprojekter",          50000,  0,      "research",    "2026-05-15", json.dumps({"marketing":20000,"pr":10000,"rekruttering":20000}),             "Udkast skrevet"),
        ("DIF Udviklingspulje",            "Træneruddannelse",              30000,  0,      "applied",     "2026-04-30", json.dumps({"rekruttering":30000}),                                         "Indsendt 15/3"),
    ]
    conn.executemany(
        '''INSERT INTO fundraising (name, description, amount_applied, amount_received, status, deadline, budget, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', grants
    )

    # Seed tasks
    tasks = [
        ("Bestil nye bolde til sommersæson",  "Lars",    "todo",    "medium", "2026-05-15", "Kontakt Sportmaster"),
        ("Opdatere hjemmeside",               "Mia",     "started", "high",   "2026-04-30", "Nye billeder fra sidste sæson"),
        ("Generalforsamling forberedelse",    "Formand", "todo",    "high",   "2026-06-10", "Find lokale, send invitationer"),
        ("Facebook opslag — tilmelding",      "Sofie",   "done",    "low",    "2026-02-20", "Udsendt 18/2"),
        ("Ansøg Lokalepulje",                 "Lars",    "started", "high",   "2026-04-28", "Deadline nærmer sig!"),
        ("Sommerfest planlægning",            "Mia",     "todo",    "medium", "2026-06-20", "Sted, mad, program"),
    ]
    conn.executemany(
        '''INSERT INTO tasks (title, assignee, status, priority, due_date, notes)
           VALUES (?, ?, ?, ?, ?, ?)''', tasks
    )

    # Seed ideas
    ideas = [
        ("Familie weekend-event",         "Overnatning på skolen + aktiviteter for hele familien", "aktivitet",      "new",       3,  "weekend, familie, event"),
        ("Sponsoraftale med lokal bager",  "Tilbyde reklameplads på hjemmeside mod støtte",         "samarbejde",     "discussed",  2,  "sponsor, økonomi"),
        ("Nyt træningsudstyr",             "Køb flere måtter og kegler til træning",                "udstyr",         "new",       -1, "indkøb, træning"),
        ("Samarbejde med naboforening",    "Fælles event i sommerferien",                           "samarbejde",     "approved",   5,  "samarbejde, sommer, event"),
        ("Digital medlemsportal",          "Online tilmelding og betaling for medlemmer",           "digitalisering", "discussed",  4,  "digital, økonomi"),
    ]
    conn.executemany(
        '''INSERT INTO ideas (title, description, category, status, vote_score, tags)
           VALUES (?, ?, ?, ?, ?, ?)''', ideas
    )

    # Seed events
    events = [
        ("DIF Ansøgningsfrist",    "2026-03-15", None,         "grant_deadline", "Ansøgningsfrist DIF",            "yearly",  0),
        ("Forårssæson start",      "2026-04-01", "2026-09-30", "season",         "Udendørs aktiviteter begynder",  "yearly",  1),
        ("Generalforsamling",      "2026-04-20", None,         "board",          "Årets generalforsamling",        "yearly",  1),
        ("Sommerlejr",             "2026-07-10", "2026-07-15", "activity",       "Sommerlejr for børn og unge",    "yearly",  1),
        ("Medlemsgebyr fornyelse", "2026-01-15", None,         "membership",     "Årsgebyr skal fornyes",          "yearly",  1),
        ("Halvårsregnskab",        "2026-06-30", None,         "reporting",      "Halvårsrapport til bestyrelsen", "yearly",  0),
        ("Hal-tider ansøgning",    "2026-05-01", None,         "facility",       "Ansøg hal-tider næste sæson",   "yearly",  0),
        ("DGI Kursusuge",          "2026-08-20", "2026-08-24", "activity",       "Kurser for trænere",             "yearly",  0),
        ("Vinterferie camp",       "2026-02-16", "2026-02-20", "activity",       "Aktiviteter i vinterferie",      "yearly",  1),
        ("Årsregnskab",            "2026-12-31", None,         "reporting",      "Årsafslutning og regnskab",      "yearly",  0),
        ("Eftersæson møde",        "2026-10-15", None,         "board",          "Evaluering af sæsonen",          "yearly",  0),
        ("Vintersæson start",      "2026-10-01", "2027-03-31", "season",         "Indendørs aktiviteter",          "yearly",  1),
    ]
    conn.executemany(
        '''INSERT INTO events (title, event_date, end_date, category, description, recurring, needs_comms)
           VALUES (?, ?, ?, ?, ?, ?, ?)''', events
    )

    # Seed content posts
    posts = [
        ("Vinterferie aktiviteter",       "facebook",  "2026-02-15", "posted",    9, "Sofie", "https://facebook.com/...", "Gode reaktioner"),
        ("Tilmelding til forårssæson",    "multiple",  "2026-03-20", "scheduled", 2, None,    None,                       "Husk link"),
        ("Generalforsamling annoncering", "facebook",  "2026-04-05", "draft",     3, None,    None,                       "Tjek dato"),
        ("Sommerlejr tilmelding åbner",   "instagram", "2026-05-01", "draft",     4, None,    None,                       ""),
    ]
    conn.executemany(
        '''INSERT INTO content_posts (title, platform, planned_date, status, event_id, posted_by, link, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', posts
    )

    conn.commit()
    conn.close()
    print("Seed data added successfully!")

if __name__ == "__main__":
    seed_all()
