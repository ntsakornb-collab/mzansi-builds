from flask import Flask, request, redirect, url_for, session, render_template, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'simplekey'


def get_db():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, description TEXT,
                  stage TEXT, support TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY, project_id INTEGER, user_id INTEGER,
                  comment TEXT, date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS milestones
                 (id INTEGER PRIMARY KEY, project_id INTEGER, title TEXT, note TEXT,
                  date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)", (name, email, pwd))
            conn.commit()
            flash('Registered! Please login.', 'success')
            return redirect('/login')
        except Exception:
            flash('Email already exists!', 'error')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, pwd)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Logged in!', 'success')
            return redirect('/feed')
        flash('Invalid credentials', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    rows = conn.execute('''
        SELECT p.id, p.title, p.stage, p.support, u.name as author
        FROM projects p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.id DESC
    ''').fetchall()
    conn.close()
    projects = [dict(r) for r in rows]
    return render_template('feed.html', projects=projects)


@app.route('/new', methods=['GET', 'POST'])
def new():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            "INSERT INTO projects (user_id, title, description, stage, support) VALUES (?,?,?,?,?)",
            (session['user_id'], request.form['title'], request.form['desc'],
             request.form['stage'], request.form['support'])
        )
        conn.commit()
        conn.close()
        flash('Project created!', 'success')
        return redirect('/feed')
    return render_template('new.html')


@app.route('/project/<int:pid>')
def project(pid):
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    proj = conn.execute('''
        SELECT p.id, p.user_id, p.title, p.description, p.stage, p.support, u.name as author
        FROM projects p
        JOIN users u ON p.user_id = u.id
        WHERE p.id=?
    ''', (pid,)).fetchone()
    if not proj:
        conn.close()
        return redirect('/feed')
    comments = conn.execute('''
        SELECT c.comment, c.date, u.name as author
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.project_id=?
        ORDER BY c.id DESC
    ''', (pid,)).fetchall()
    milestones = conn.execute('''
        SELECT title, note, date FROM milestones
        WHERE project_id=?
        ORDER BY id ASC
    ''', (pid,)).fetchall()
    conn.close()
    project_data = {
        'id': proj['id'],
        'user_id': proj['user_id'],
        'title': proj['title'],
        'desc': proj['description'],
        'stage': proj['stage'],
        'support': proj['support'],
        'author': proj['author'],
    }
    comments_data = [{'author': c['author'], 'comment': c['comment'], 'date': c['date']} for c in comments]
    milestones_data = [{'title': m['title'], 'note': m['note'], 'date': m['date']} for m in milestones]
    return render_template('project.html', project=project_data, comments=comments_data, milestones=milestones_data)


@app.route('/project/<int:pid>/comment', methods=['POST'])
def comment(pid):
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    conn.execute(
        "INSERT INTO comments (project_id, user_id, comment) VALUES (?,?,?)",
        (pid, session['user_id'], request.form['comment'])
    )
    conn.commit()
    conn.close()
    flash('Comment added!', 'success')
    return redirect(f'/project/{pid}')


@app.route('/project/<int:pid>/raise', methods=['POST'])
def raise_hand(pid):
    if 'user_id' not in session:
        return redirect('/login')
    flash('Collaboration request sent to project owner!', 'success')
    return redirect(f'/project/{pid}')


@app.route('/project/<int:pid>/milestone', methods=['POST'])
def add_milestone(pid):
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    proj = conn.execute("SELECT user_id FROM projects WHERE id=?", (pid,)).fetchone()
    if proj and proj['user_id'] == session['user_id']:
        conn.execute(
            "INSERT INTO milestones (project_id, title, note) VALUES (?,?,?)",
            (pid, request.form['milestone_title'], request.form.get('milestone_note', ''))
        )
        conn.commit()
        flash('Milestone logged!', 'success')
    conn.close()
    return redirect(f'/project/{pid}')


@app.route('/project/<int:pid>/update', methods=['POST'])
def update_stage(pid):
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    proj = conn.execute("SELECT user_id FROM projects WHERE id=?", (pid,)).fetchone()
    if proj and proj['user_id'] == session['user_id']:
        conn.execute("UPDATE projects SET stage=? WHERE id=?", (request.form['new_stage'], pid))
        conn.commit()
        flash('Progress updated!', 'success')
    conn.close()
    return redirect(f'/project/{pid}')


@app.route('/wall')
def wall():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    rows = conn.execute('''
        SELECT p.title, u.name as author
        FROM projects p
        JOIN users u ON p.user_id = u.id
        WHERE p.stage='completed'
    ''').fetchall()
    conn.close()
    projects = [dict(r) for r in rows]
    return render_template('wall.html', projects=projects)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
