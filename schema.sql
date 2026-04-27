-- fundraising: individual grants/donations
CREATE TABLE IF NOT EXISTS fundraising (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  amount_applied INTEGER,
  amount_received INTEGER,
  status TEXT DEFAULT 'identified', -- identified/applied/approved/rejected/received
  deadline DATE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- fund_pipeline: funds to apply for (research list)
CREATE TABLE IF NOT EXISTS fund_pipeline (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_name TEXT NOT NULL,
  description TEXT,
  amount_estimate INTEGER,
  deadline DATE,
  status TEXT DEFAULT 'todo', -- todo/in_progress/submitted/skip
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tasks: with assignee
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  assignee TEXT,
  status TEXT DEFAULT 'todo', -- todo/started/done
  priority TEXT DEFAULT 'medium',
  due_date DATE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ideas
CREATE TABLE IF NOT EXISTS ideas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,
  status TEXT DEFAULT 'new', -- new/discussed/approved/archived
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- events (for årshjul)
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  event_date DATE NOT NULL,
  end_date DATE,
  category TEXT, -- grant_deadline/activity/board/season/membership/reporting/facility
  description TEXT,
  recurring TEXT, -- null/yearly/monthly
  needs_comms INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- content posts (communications)
CREATE TABLE IF NOT EXISTS content_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  platform TEXT, -- facebook/instagram/linkedin/multiple
  planned_date DATE,
  status TEXT DEFAULT 'draft', -- draft/scheduled/posted
  event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
  posted_by TEXT,
  link TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);