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
        "modules": ["fundraising", "fund_pipeline", "tasks", "ideas", "events"]
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
        '''INSERT INTO events (title, event_date, end_date, category, description, recurring)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data.get('title'), data.get('event_date'), data.get('end_date'),
         data.get('category'), data.get('description'), data.get('recurring'))
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
        '''UPDATE events SET title=?, event_date=?, end_date=?, category=?, description=?, recurring=?
           WHERE id=?''',
        (data.get('title'), data.get('event_date'), data.get('end_date'),
         data.get('category'), data.get('description'), data.get('recurring'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM events WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ── static files ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
