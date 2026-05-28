from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            priority TEXT DEFAULT 'Low'
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid login"

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('todo.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect('/login')

    filter_status = request.args.get('filter', 'all')
    search = request.args.get('search', '')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE user_id=?"
    values = [session['user_id']]

    if search:
        query += " AND task LIKE ?"
        values.append('%' + search + '%')

    if filter_status == 'pending':
        query += " AND status='Pending'"
    elif filter_status == 'completed':
        query += " AND status='Completed'"

    cursor.execute(query, values)
    tasks = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (session['user_id'],))
    total_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Completed'",
                   (session['user_id'],))
    completed_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Pending'",
                   (session['user_id'],))
    pending_tasks = cursor.fetchone()[0]

    conn.close()

    return render_template("index.html",
                           tasks=tasks,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           pending_tasks=pending_tasks)

# ---------------- ADD ----------------
@app.route('/add', methods=['POST'])
def add():

    task = request.form['task']
    due_date = request.form['due_date']
    priority = request.form['priority']

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (user_id, task, status, due_date, priority)
        VALUES (?, ?, 'Pending', ?, ?)
    """, (session['user_id'], task, due_date, priority))

    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- COMPLETE ----------------
@app.route('/complete/<int:id>')
def complete(id):

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE tasks SET status='Completed' WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- EDIT PAGE ----------------
@app.route('/edit/<int:id>')
def edit(id):

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id=?", (id,))
    task = cursor.fetchone()

    conn.close()

    return render_template("edit.html", task=task)

# ---------------- UPDATE ----------------
@app.route('/update/<int:id>', methods=['POST'])
def update(id):

    task = request.form['task']
    due_date = request.form['due_date']
    priority = request.form['priority']

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET task=?, due_date=?, priority=?
        WHERE id=?
    """, (task, due_date, priority, id))

    conn.commit()
    conn.close()

    return redirect('/')

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)