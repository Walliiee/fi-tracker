import os
from flask import Flask, jsonify, request, send_from_directory
import db as db_module

app = Flask(__name__, static_folder='static', template_folder='templates')

db_module.init_db()

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error('Unhandled exception: %s', e, exc_info=True)
    return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

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
    # Support partial update: fetch existing, merge
    existing = conn.execute('SELECT * FROM fundraising WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    existing = dict(existing)
    merged = {**existing, **data}
    conn.execute(
        '''UPDATE fundraising SET name=?, amount_applied=?, amount_received=?, status=?, deadline=?, notes=?
           WHERE id=?''',
        (merged['name'], merged.get('amount_applied'), merged.get('amount_received'),
         merged['status'], merged.get('deadline'), merged.get('notes'), id)
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
    rows = conn.execute('SELECT * FROM ideas ORDER BY vote_score DESC, created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ideas', methods=['POST'])
def create_idea():
    data = request.json
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO ideas (title, description, category, status, vote_score, tags)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('description'), data.get('category'),
         data.get('status', 'new'), data.get('vote_score', 0), data.get('tags', ''))
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
        '''UPDATE ideas SET title=?, description=?, category=?, status=?, vote_score=?, tags=? WHERE id=?''',
        (data.get('title'), data.get('description'), data.get('category'), data.get('status'),
         data.get('vote_score', 0), data.get('tags', ''), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── events (årshjul) ───────────────────────────────────────────────────────────
@app.route('/api/ideas/<int:id>/vote', methods=['POST'])
def vote_idea(id):
    data = request.json
    direction = data.get('direction', 0)  # +1 or -1
    conn = db_module.get_db()
    conn.execute('UPDATE ideas SET vote_score = vote_score + ? WHERE id=?', (direction, id))
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/ideas/<int:id>/approve', methods=['POST'])
def approve_idea(id):
    conn = db_module.get_db()
    # Update idea status
    conn.execute('UPDATE ideas SET status="approved" WHERE id=?', (id,))
    # Get idea title for task
    idea = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    if idea:
        conn.execute(
            '''INSERT INTO tasks (title, assignee, status, priority, due_date, notes)
               VALUES (?, NULL, "todo", "medium", NULL, ?)''',
            (idea['title'], f'From approved idea #{id}')
        )
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

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
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=debug)

# ── CSV export helpers ────────────────────────────────────────────────────────
def _csv_response(rows, module):
    from flask import make_response
    import csv
    from io import StringIO
    import datetime
    today = datetime.date.today().isoformat()
    output = StringIO()
    if not rows:
        output.write('')
    else:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename=fi-tracker-{module}-{today}.csv'
    return resp


# ── CSV export endpoints ──────────────────────────────────────────────────────
@app.route('/api/export/fundraising', methods=['GET'])
def export_fundraising():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fundraising ORDER BY created_at DESC').fetchall()
    conn.close()
    return _csv_response(rows, 'fundraising')

@app.route('/api/export/tasks', methods=['GET'])
def export_tasks():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    conn.close()
    return _csv_response(rows, 'tasks')

@app.route('/api/export/ideas', methods=['GET'])
def export_ideas():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM ideas ORDER BY vote_score DESC, created_at DESC').fetchall()
    conn.close()
    return _csv_response(rows, 'ideas')

@app.route('/api/export/events', methods=['GET'])
def export_events():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM events ORDER BY event_date ASC').fetchall()
    conn.close()
    return _csv_response(rows, 'events')

@app.route('/api/export/fund-pipeline', methods=['GET'])
def export_fund_pipeline():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fund_pipeline ORDER BY deadline ASC').fetchall()
    conn.close()
    return _csv_response(rows, 'fund-pipeline')

@app.route('/api/export/content-posts', methods=['GET'])
def export_content_posts():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM content_posts ORDER BY planned_date ASC').fetchall()
    conn.close()
    return _csv_response(rows, 'content-posts')


# ── Ollama AI report generator ────────────────────────────────────────────────
@app.route('/api/report', methods=['POST'])
def generate_report():
    from datetime import datetime, timedelta
    import urllib.request, urllib.error, json

    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')

    data = request.json or {}
    today = datetime.now().date()
    default_from = (today - timedelta(days=30)).isoformat()
    default_to = today.isoformat()
    from_date = data.get('from_date', default_from)
    to_date = data.get('to_date', default_to)

    conn = db_module.get_db()

    # Tasks
    tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    open_tasks = [t for t in tasks if t['status'] != 'done']
    overdue_tasks = [t for t in tasks if t['status'] != 'done' and t['due_date'] and t['due_date'] < today.isoformat()]
    assignees = {}
    for t in tasks:
        a = t['assignee'] or 'Unassigned'
        assignees[a] = assignees.get(a, 0) + 1
    top_assignees = sorted(assignees.items(), key=lambda x: -x[1])[:3]

    # Fundraising
    fr_rows = conn.execute('SELECT * FROM fundraising ORDER BY created_at DESC').fetchall()
    total_applied = sum(r['amount_applied'] or 0 for r in fr_rows)
    total_received = sum(r['amount_received'] or 0 for r in fr_rows)
    win_rate = round(total_received / total_applied * 100, 1) if total_applied > 0 else 0
    fr_statuses = {}
    for r in fr_rows:
        s = r['status'] or 'unknown'
        fr_statuses[s] = fr_statuses.get(s, 0) + 1
    upcoming_deadlines = [r for r in fr_rows if r['deadline'] and r['deadline'] >= today.isoformat() and r['status'] in ('identified','applied','approved')]
    upcoming_deadlines.sort(key=lambda x: x['deadline'])

    # Ideas
    idea_rows = conn.execute('SELECT * FROM ideas ORDER BY vote_score DESC, created_at DESC').fetchall()
    ideas_in_range = [i for i in idea_rows if i['created_at'] and from_date <= i['created_at'][:10] <= to_date]
    top_voted = [i for i in idea_rows if i['vote_score'] and i['vote_score'] > 0][:3]
    approved_count = len([i for i in idea_rows if i['status'] == 'approved'])

    # Events
    event_rows = conn.execute('SELECT * FROM events ORDER BY event_date ASC').fetchall()
    upcoming_events = [e for e in event_rows if e['event_date'] and from_date <= e['event_date'] <= to_date]
    needs_comms_count = len([e for e in event_rows if e['needs_comms']])

    # Communications
    posts = conn.execute('SELECT * FROM content_posts ORDER BY planned_date DESC').fetchall()
    posts_in_range = [p for p in posts if p['planned_date'] and from_date <= p['planned_date'] <= to_date]
    posted_count = len([p for p in posts if p['status'] == 'posted'])

    conn.close()

    stats = {
        'from_date': from_date,
        'to_date': to_date,
        'tasks': {
            'total': len(tasks),
            'open': len(open_tasks),
            'overdue': len(overdue_tasks),
            'top_assignees': top_assignees,
        },
        'fundraising': {
            'total_applied': total_applied,
            'total_received': total_received,
            'win_rate': win_rate,
            'status_breakdown': fr_statuses,
            'upcoming_deadlines': [(r['name'], r['deadline']) for r in upcoming_deadlines[:5]],
        },
        'ideas': {
            'new_in_range': len(ideas_in_range),
            'total': len(idea_rows),
            'approved': approved_count,
            'top_voted': [(i['title'], i['vote_score']) for i in top_voted],
        },
        'events': {
            'in_range': len(upcoming_events),
            'total_needs_comms': needs_comms_count,
        },
        'communications': {
            'posts_in_range': len(posts_in_range),
            'posted_total': posted_count,
        }
    }

    prompt = f"""Du er en dansk foreningsassistent der skriver et kort, venligt management-resume for Familieidræt.

## Data fra {from_date} til {to_date}

**Opgaver:** {stats['tasks']['open']} aabne, {stats['tasks']['overdue']} overskredet. Top-assignees: {', '.join(f'{a}({n})' for a,n in stats['tasks']['top_assignees']) if stats['tasks']['top_assignees'] else 'ingen'}.

**Fundraising:** {stats['fundraising']['total_applied']:,} kr ansoegt, {stats['fundraising']['total_received']:,} kr modtaget. Win rate: {stats['fundraising']['win_rate']}%. Status: {', '.join(f'{k}: {v}' for k,v in stats['fundraising']['status_breakdown'].items()) if stats['fundraising']['status_breakdown'] else 'ingen'}. Kommende deadlines: {', '.join(f'{n} ({d})' for n,d in stats['fundraising']['upcoming_deadlines']) if stats['fundraising']['upcoming_deadlines'] else 'ingen'}.

**Ideer:** {stats['ideas']['new_in_range']} nye ideer i perioden. {stats['ideas']['approved']} godkendt i alt. Top stemmer: {', '.join(f'{t} ({v})' for t,v in stats['ideas']['top_voted']) if stats['ideas']['top_voted'] else 'ingen'}.

**Begivenheder:** {stats['events']['in_range']} i perioden. {stats['events']['total_needs_comms']} events mangler kommunikation.

**Indhold:** {stats['communications']['posts_in_range']} opslag i perioden. {stats['communications']['posted_total']} posted i alt.

Skriv et kort resume pa 3-5 punkter pa dansk. Vaer konkret, ikke generisk. Naevn tal. Brug bindestreg - for punkter, ikke asterisk."""

    try:
        req = urllib.request.Request(
            f'{OLLAMA_URL}/api/generate',
            data=json.dumps({'model': os.environ.get('OLLAMA_MODEL', 'minimax-m2.7:cloud'), 'prompt': prompt, 'stream': False}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            ai_text = result.get('response', '').strip()
    except Exception:
        ai_text = None

    if ai_text:
        return jsonify({'report': ai_text, 'stats': stats})
    else:
        fallback = f"AI-model er ikke tilgaengelig. Raadata:\n\n"
        fallback += f"- Opgaver: {stats['tasks']['open']} aabne, {stats['tasks']['overdue']} overskredet\n"
        fallback += f"- Fundraising: {stats['fundraising']['total_applied']:,} kr ansoegt, {stats['fundraising']['total_received']:,} kr modtaget ({stats['fundraising']['win_rate']}% win rate)\n"
        fallback += f"- Ideer: {stats['ideas']['new_in_range']} nye, {stats['ideas']['approved']} godkendt\n"
        fallback += f"- Events: {stats['events']['in_range']} i perioden, {stats['events']['total_needs_comms']} mangler comms\n"
        fallback += f"- Indhold: {stats['communications']['posts_in_range']} opslag i perioden\n"
        return jsonify({'report': fallback, 'stats': stats})
