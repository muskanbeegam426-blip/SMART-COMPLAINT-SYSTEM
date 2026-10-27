import os
import sqlite3
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'smart_complaint_secret'

if os.path.exists('/tmp'):
    DB_PATH = '/tmp/complaint.db'
else:
    DB_PATH = 'complaint.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, email TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS complaints 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, title TEXT, description TEXT, 
                  category TEXT, status TEXT DEFAULT 'Pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'citizen')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)", 
                      (name,email,password,role))
            conn.commit()
        except:
            pass
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
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
    return render_template('login.html')

@app.route('/citizen_dashboard', methods=['GET','POST'])
def citizen_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO complaints (user_id,title,description,category) VALUES (?,?,?,?)",
                  (session['user_id'],title,description,category))
        conn.commit()
        conn.close()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM complaints WHERE user_id=?", (session['user_id'],))
    complaints = c.fetchall()
    conn.close()
    return render_template('citizen_dashboard.html', complaints=complaints)

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
