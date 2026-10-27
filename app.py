import os
import sqlite3
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'smart_complaint_secret_key_2024_muskaan_fixed_final'

if os.path.exists('/tmp'):
    DB_PATH = '/tmp/complaint.db'
else:
    DB_PATH = 'complaint.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS complaints
                 (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, description TEXT, category TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", (name, email, password, role))
            conn.commit()
            conn.close()
            return redirect('/login')
        except Exception as e:
            return f"Error: {e} - Email already exists"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            if user[4] == 'admin':
                return redirect('/admin_dashboard')
            else:
                return redirect('/citizen_dashboard')
        else:
            return "Invalid email or password! Go back and try again."
    return render_template('login.html')

@app.route('/citizen_dashboard', methods=['GET', 'POST'])
def citizen_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        # FIX: .get() will not give Bad Request if empty
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO complaints (user_id, title, description, category, status) VALUES (?, ?, ?, ?, ?)",
                  (session['user_id'], title, description, category, 'Pending'))
        conn.commit()
        conn.close()
        return redirect('/citizen_dashboard')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM complaints WHERE user_id=?", (session['user_id'],))
    complaints = c.fetchall()
    conn.close()
    return render_template('citizen_dashboard.html', complaints=complaints, name=session.get('name'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM complaints")
    complaints = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', complaints=complaints)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
