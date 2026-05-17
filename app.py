import os
import json
import logging
import time
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory, session, redirect
import db as db_module
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))


_db_initialized = False

def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        db_module.init_db()
        _db_initialized = True


# ── Authentication ───────────────────────────────────────────────────────────
@app.before_request
def _require_auth():
    if request.endpoint in ('health', 'static', 'login', 'api_login', 'csrf_token', None):
        return None
    
    # If the user is trying to access the index page without auth, redirect to login
    if request.endpoint == 'index' and not session.get('user_id'):
        return redirect('/login')

    # For API endpoints, return 401
    if request.path.startswith('/api/') and not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/login', methods=['GET'])
def login():
    if session.get('user_id'):
        return redirect('/')
    return send_from_directory('templates', 'login.html')

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    conn = db_module.get_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        # Session cookie is automatically secure/httponly in Flask
        return jsonify({'message': 'Logged in', 'user': {'id': user['id'], 'name': user['name'], 'role': user['role']}})
        
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({
        'id': session['user_id'],
        'name': session['user_name'],
        'role': session['user_role']
    })

@app.before_request
def _init_on_first_request():
    _ensure_db()

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error('Unhandled exception: %s', e, exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

def _require(data, *fields):
    """Return a 400 error response if any required field is missing/blank, else None."""
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    return None


# CSRF: generate token on GET, validate on state-changing methods
@app.before_request
def csrf_middleware():
    if request.endpoint == 'csrf_token':
        return None
    if request.method in ('GET', 'HEAD'):
        # Only set if not already present (endpoint or after_request handles it)
        if not request.cookies.get('csrf_token'):
            token = secrets.token_hex(16)
            request._csrf_token = token
        return None
    if request.method in ('POST', 'PUT', 'DELETE'):
        cookie_token = request.cookies.get('csrf_token')
        header_token = request.headers.get('X-CSRF-Token')
        if not cookie_token or cookie_token != header_token:
            return jsonify({'error': 'CSRF token missing or invalid'}), 403
    return None

@app.after_request
def csrf_cookie(response):
    if request.method in ('GET', 'HEAD') and hasattr(request, '_csrf_token'):
        response.set_cookie('csrf_token', request._csrf_token, httponly=True, samesite='Strict')
    return response

@app.route('/api/csrf-token', methods=['GET'])
def csrf_token():
    token = request.cookies.get('csrf_token')
    if not token:
        token = secrets.token_hex(16)
        request._csrf_token = token
    resp = jsonify({'csrf_token': token})
    return resp

# ── health ───────────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    try:
        conn = db_module.get_db()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        app.logger.error('Health check failed: %s', e)
        return jsonify({'status': 'error', 'detail': str(e)}), 503

# ── status ──────────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "ok",
        "app": "fi-tracker",
        "modules": ["fundraising", "fund_pipeline", "tasks", "ideas", "events", "content_posts"]
    })

# ── fundraising ─────────────────────────────────────────────────────────────
def _parse_budget(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}

def _serialize_row(row):
    d = dict(row)
    if 'budget' in d:
        d['budget'] = _parse_budget(d['budget'])
    return d

@app.route('/api/fundraising', methods=['GET'])
def get_fundraising():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fundraising ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([_serialize_row(r) for r in rows])

@app.route('/api/fundraising', methods=['POST'])
def create_fundraising():
    data = request.json or {}
    err = _require(data, 'name')
    if err:
        return err
    budget = json.dumps(_parse_budget(data.get('budget')))
    conn = db_module.get_db()
    cur = conn.execute(
        '''INSERT INTO fundraising (name, description, amount_applied, amount_received, status, deadline, budget, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (data.get('name'), data.get('description'), data.get('amount_applied'), data.get('amount_received'),
         data.get('status', 'identified'), data.get('deadline'), budget, data.get('notes'))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fundraising WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    app.logger.info('fundraising created id=%s name=%s', cur.lastrowid, data.get('name'))
    return jsonify(_serialize_row(row)), 201

@app.route('/api/fundraising/<int:id>', methods=['PUT', 'DELETE'])
def handle_fundraising(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM fundraising WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM fundraising WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('fundraising deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM fundraising WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    existing = dict(existing)
    merged = {**existing, **data}
    budget = json.dumps(_parse_budget(merged.get('budget')))
    conn.execute(
        '''UPDATE fundraising SET name=?, description=?, amount_applied=?, amount_received=?,
           status=?, deadline=?, budget=?, notes=? WHERE id=?''',
        (merged['name'], merged.get('description'), merged.get('amount_applied'), merged.get('amount_received'),
         merged['status'], merged.get('deadline'), budget, merged.get('notes'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fundraising WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(_serialize_row(row))

# ── fund_pipeline ────────────────────────────────────────────────────────────
@app.route('/api/fund-pipeline', methods=['GET'])
def get_fund_pipeline():
    conn = db_module.get_db()
    rows = conn.execute('SELECT * FROM fund_pipeline ORDER BY deadline ASC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/fund-pipeline', methods=['POST'])
def create_fund_pipeline():
    data = request.json or {}
    err = _require(data, 'fund_name')
    if err:
        return err
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
    app.logger.info('fund_pipeline created id=%s name=%s', cur.lastrowid, data.get('fund_name'))
    return jsonify(dict(row)), 201

@app.route('/api/fund-pipeline/<int:id>', methods=['PUT', 'DELETE'])
def handle_fund_pipeline(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM fund_pipeline WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM fund_pipeline WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('fund_pipeline deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM fund_pipeline WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    merged = {**dict(existing), **data}
    conn.execute(
        '''UPDATE fund_pipeline SET fund_name=?, description=?, amount_estimate=?, deadline=?, status=?, notes=?
           WHERE id=?''',
        (merged.get('fund_name'), merged.get('description'), merged.get('amount_estimate'),
         merged.get('deadline'), merged.get('status'), merged.get('notes'), id)
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
    data = request.json or {}
    err = _require(data, 'title')
    if err:
        return err
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
    app.logger.info('task created id=%s title=%s', cur.lastrowid, data.get('title'))
    return jsonify(dict(row)), 201

@app.route('/api/tasks/<int:id>', methods=['PUT', 'DELETE'])
def handle_task(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM tasks WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM tasks WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('task deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM tasks WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    merged = {**dict(existing), **data}
    conn.execute(
        '''UPDATE tasks SET title=?, assignee=?, status=?, priority=?, due_date=?, notes=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?''',
        (merged.get('title'), merged.get('assignee'), merged.get('status'), merged.get('priority'),
         merged.get('due_date'), merged.get('notes'), id)
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
    data = request.json or {}
    err = _require(data, 'title')
    if err:
        return err
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
    app.logger.info('idea created id=%s title=%s', cur.lastrowid, data.get('title'))
    return jsonify(dict(row)), 201

@app.route('/api/ideas/<int:id>', methods=['PUT', 'DELETE'])
def handle_idea(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM ideas WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM ideas WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('idea deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    merged = {**dict(existing), **data}
    conn.execute(
        '''UPDATE ideas SET title=?, description=?, category=?, status=?, vote_score=?, tags=? WHERE id=?''',
        (merged.get('title'), merged.get('description'), merged.get('category'), merged.get('status'),
         merged.get('vote_score', 0), merged.get('tags', ''), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM ideas WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── events (årshjul) ───────────────────────────────────────────────────────────
@app.route('/api/ideas/<int:id>/vote', methods=['POST'])
def vote_idea(id):
    data = request.json or {}
    direction = data.get('direction', 0)
    if direction not in (1, -1):
        return jsonify({'error': 'direction must be 1 or -1'}), 400
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
    data = request.json or {}
    err = _require(data, 'title', 'event_date')
    if err:
        return err
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
    app.logger.info('event created id=%s title=%s date=%s', cur.lastrowid, data.get('title'), data.get('event_date'))
    return jsonify(dict(row)), 201

@app.route('/api/events/<int:id>', methods=['PUT', 'DELETE'])
def handle_event(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM events WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM events WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('event deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM events WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    merged = {**dict(existing), **data}
    conn.execute(
        '''UPDATE events SET title=?, event_date=?, end_date=?, category=?, description=?, recurring=?, needs_comms=?
           WHERE id=?''',
        (merged.get('title'), merged.get('event_date'), merged.get('end_date'),
         merged.get('category'), merged.get('description'), merged.get('recurring'),
         merged.get('needs_comms', 0), id)
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
    data = request.json or {}
    err = _require(data, 'title')
    if err:
        return err
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
    app.logger.info('content_post created id=%s title=%s', cur.lastrowid, data.get('title'))
    return jsonify(dict(row)), 201

@app.route('/api/content-posts/<int:id>', methods=['PUT', 'DELETE'])
def handle_content_post(id):
    conn = db_module.get_db()
    if request.method == 'DELETE':
        existing = conn.execute('SELECT id FROM content_posts WHERE id=?', (id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        conn.execute('DELETE FROM content_posts WHERE id=?', (id,))
        conn.commit()
        conn.close()
        app.logger.info('content_post deleted id=%s', id)
        return jsonify({'deleted': id})
    data = request.json
    existing = conn.execute('SELECT * FROM content_posts WHERE id=?', (id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    merged = {**dict(existing), **data}
    conn.execute(
        '''UPDATE content_posts SET title=?, platform=?, planned_date=?, status=?, event_id=?, posted_by=?, link=?, notes=?
           WHERE id=?''',
        (merged.get('title'), merged.get('platform'), merged.get('planned_date'),
         merged.get('status'), merged.get('event_id'), merged.get('posted_by'),
         merged.get('link'), merged.get('notes'), id)
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


# ── rate limiting helper ─────────────────────────────────────────────────────
_report_last_call = 0
_REPORT_COOLDOWN = 30  # seconds

def _check_report_rate():
    global _report_last_call
    now = time.time()
    if now - _report_last_call < _REPORT_COOLDOWN:
        return False
    _report_last_call = now
    return True

# ── Ollama AI report generator ────────────────────────────────────────────────
@app.route('/api/report', methods=['POST'])
def generate_report():
    if not _check_report_rate():
        return jsonify({'error': 'Too many requests — please wait 30 seconds'}), 429
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

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=debug)
