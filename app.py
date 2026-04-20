from flask import Flask, jsonify, request, send_from_directory
import db as db_module

app = Flask(__name__, static_folder='static', template_folder='templates')

db_module.init_db()

# ── status ──────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "ok",
        "app": "fi-tracker",
        "modules": ["fundraising", "fund_pipeline", "tasks", "ideas", "events", "content_posts"]
    })

# ── fundraising ─────────────────────────────────────────────────────────────
@app.route('/api/fundraising', methods=['GET'])
def get_fundraising():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fundraising ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/fundraising', methods=['POST'])
def create_fundraising():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO fundraising (name, amount_applied, amount_received, status, deadline, notes)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data.get('name'), data.get('amount_applied'), data.get('amount_received'),
         data.get('status', 'identified'), data.get('deadline'), data.get('notes'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fundraising WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/fundraising/<int:id>', methods=['PUT', 'DELETE'])
def handle_fundraising(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM fundraising WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE fundraising SET name=?, amount_applied=?, amount_received=?, status=?, deadline=?, notes=?
           WHERE id=?''',
        (data.get('name'), data.get('amount_applied'), data.get('amount_received'),
         data.get('status'), data.get('deadline'), data.get('notes'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fundraising WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── fund_pipeline ────────────────────────────────────────────────────────────
@app.route('/api/fund-pipeline', methods=['GET'])
def get_fund_pipeline():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fund_pipeline ORDER BY deadline ASC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/fund-pipeline', methods=['POST'])
def create_fund_pipeline():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO fund_pipeline (fund_name, description, amount_estimate, deadline, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data.get('fund_name'), data.get('description'), data.get('amount_estimate'),
         data.get('deadline'), data.get('status', 'todo'), data.get('notes'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fund_pipeline WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/fund-pipeline/<int:id>', methods=['PUT', 'DELETE'])
def handle_fund_pipeline(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM fund_pipeline WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE fund_pipeline SET fund_name=?, description=?, amount_estimate=?, deadline=?, status=?, notes=?
           WHERE id=?''',
        (data.get('fund_name'), data.get('description'), data.get('amount_estimate'),
         data.get('deadline'), data.get('status'), data.get('notes'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fund_pipeline WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── tasks (with assignee) ─────────────────────────────────────────────────────
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO tasks (title, assignee, status, priority, due_date, notes)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('assignee'), data.get('status', 'todo'),
         data.get('priority', 'medium'), data.get('due_date'), data.get('notes'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM tasks WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/tasks/<int:id>', methods=['PUT', 'DELETE'])
def handle_task(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM tasks WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE tasks SET title=?, assignee=?, status=?, priority=?, due_date=?, notes=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?''',
        (data.get('title'), data.get('assignee'), data.get('status'), data.get('priority'),
         data.get('due_date'), data.get('notes'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM tasks WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── ideas ─────────────────────────────────────────────────────────────────────
@app.route('/api/ideas', methods=['GET'])
def get_ideas():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM ideas ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ideas', methods=['POST'])
def create_idea():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO ideas (title, description, category, status)
           VALUES (?, ?, ?, ?)''',
        (data.get('title'), data.get('description'), data.get('category'),
         data.get('status', 'new'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/ideas/<int:id>', methods=['PUT', 'DELETE'])
def handle_idea(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM ideas WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE ideas SET title=?, description=?, category=?, status=? WHERE id=?''',
        (data.get('title'), data.get('description'), data.get('category'), data.get('status'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── events (årshjul) ───────────────────────────────────────────────────────────
@app.route('/api/events', methods=['GET'])
def get_events():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM events ORDER BY event_date ASC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO events (title, event_date, end_date, category, description, recurring, needs_comms)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('event_date'), data.get('end_date'),
         data.get('category'), data.get('description'), data.get('recurring'),
         data.get('needs_comms', 0))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM events WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/events/<int:id>', methods=['PUT', 'DELETE'])
def handle_event(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM events WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE events SET title=?, event_date=?, end_date=?, category=?, description=?, recurring=?, needs_comms=?
           WHERE id=?''',
        (data.get('title'), data.get('event_date'), data.get('end_date'),
         data.get('category'), data.get('description'), data.get('recurring'),
         data.get('needs_comms', 0), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM events WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── content posts (communications) ──────────────────────────────────────────────
@app.route('/api/content-posts', methods=['GET'])
def get_content_posts():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM content_posts ORDER BY planned_date ASC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/content-posts', methods=['POST'])
def create_content_post():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO content_posts (title, platform, planned_date, status, event_id, posted_by, link, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('platform'), data.get('planned_date'),
         data.get('status', 'draft'), data.get('event_id'), data.get('posted_by'),
         data.get('link'), data.get('notes'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM content_posts WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/content-posts/<int:id>', methods=['PUT', 'DELETE'])
def handle_content_post(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM content_posts WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'deleted': id})
    data = request.json
    conn.execute(
        '''UPDATE content_posts SET title=?, platform=?, planned_date=?, status=?, event_id=?, posted_by=?, link=?, notes=?
           WHERE id=?''',
        (data.get('title'), data.get('platform'), data.get('planned_date'),
         data.get('status'), data.get('event_id'), data.get('posted_by'),
         data.get('link'), data.get('notes'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM content_posts WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/content-posts/by-event/<int:event_id>', methods=['GET'])
def get_content_posts_by_event(event_id):
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM content_posts WHERE event_id=? ORDER BY planned_date ASC', (event_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── dashboard ─────────────────────────────────────────────────────────────────
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    from datetime import datetime, timedelta
    conn = db_module.get_db()
    today = datetime.now().date()
    future_60 = today + timedelta(days=60)
    future_30 = today + timedelta(days=30)

    # 1. Open Tasks — count + 3 most urgent
    tasks = conn.execute('SELECT * FROM tasks WHERE status != "done" ORDER BY due_date ASC NULLS LAST, created_at ASC').fetchall()
    open_tasks_count = len(tasks)
    urgent_tasks = [dict(r) for r in tasks[:3]]

    # 2. Upcoming Deadlines — next 5 årshjul events within 60 days
    events = conn.execute(
        'SELECT * FROM events WHERE event_date >= ? AND event_date <= ? ORDER BY event_date ASC LIMIT 5',
        (today.isoformat(), future_60.isoformat())
    ).fetchall()
    upcoming_events = [dict(r) for r in events]

    # 3. Fundraising Totals
    fr_sums = conn.execute(
        'SELECT SUM(amount_received) as total_received, SUM(amount_applied) as total_applied FROM fundraising'
    ).fetchone()
    total_received = fr_sums['total_received'] or 0
    total_applied = fr_sums['total_applied'] or 0

    # 4. Posts Due — events with needs_comms=1 but no linked post
    needs_comms_events = conn.execute('SELECT id FROM events WHERE needs_comms = 1').fetchall()
    needs_comms_ids = [r['id'] for r in needs_comms_events]
    posts_due = 0
    if needs_comms_ids:
        placeholders = ','.join('?' for _ in needs_comms_ids)
        linked_event_ids = conn.execute(
            f'SELECT DISTINCT event_id FROM content_posts WHERE event_id IN ({placeholders})',
            needs_comms_ids
        ).fetchall()
        linked_ids = set(r['event_id'] for r in linked_event_ids if r['event_id'])
        posts_due = len(set(needs_comms_ids) - linked_ids)

    # 5. Recent Activity — last 5 items from all modules
    recent = []
    # Tasks
    task_rows = conn.execute('SELECT id, title, created_at, "task" as module FROM tasks ORDER BY created_at DESC LIMIT 5').fetchall()
    recent.extend([dict(r) for r in task_rows])
    # Fundraising
    fr_rows = conn.execute('SELECT id, name as title, created_at, "fundraising" as module FROM fundraising ORDER BY created_at DESC LIMIT 5').fetchall()
    recent.extend([dict(r) for r in fr_rows])
    # Ideas
    idea_rows = conn.execute('SELECT id, title, created_at, "idea" as module FROM ideas ORDER BY created_at DESC LIMIT 5').fetchall()
    recent.extend([dict(r) for r in idea_rows])
    # Content Posts
    post_rows = conn.execute('SELECT id, title, created_at, "post" as module FROM content_posts ORDER BY created_at DESC LIMIT 5').fetchall()
    recent.extend([dict(r) for r in post_rows])
    # Events
    event_rows = conn.execute('SELECT id, title, created_at, "event" as module FROM events ORDER BY created_at DESC LIMIT 5').fetchall()
    recent.extend([dict(r) for r in event_rows])

    # Sort by created_at desc and take top 5
    recent.sort(key=lambda x: x['created_at'] or '', reverse=True)
    recent = recent[:5]

    # Next 30 days banner events
    next_30_events = conn.execute(
        'SELECT * FROM events WHERE event_date >= ? AND event_date <= ? ORDER BY event_date ASC',
        (today.isoformat(), future_30.isoformat())
    ).fetchall()
    next_30 = [dict(r) for r in next_30_events]

    conn.close()

    return jsonify({
        'open_tasks': {
            'count': open_tasks_count,
            'urgent': urgent_tasks
        },
        'upcoming_events': {
            'count': len(upcoming_events),
            'events': upcoming_events
        },
        'fundraising': {
            'total_received': total_received,
            'total_applied': total_applied
        },
        'posts_due': posts_due,
        'recent_activity': recent,
        'next_30_days': next_30
    })

# ── static files ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)