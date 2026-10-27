from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'smartcomplaint123'

def init_db():
    conn = sqlite3.connect('complaint.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT)''')
    # UPDATED TABLE WITH LOCATION
    c.execute('''CREATE TABLE IF NOT EXISTS complaints
                 (id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, description TEXT, area TEXT, landmark TEXT, urgency TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO users (id, name, email, password, role) VALUES (1, 'Admin', 'admin@smartcity.com', 'admin123', 'admin')")
    conn.commit()
    conn.close()

def get_urgency(text):
    text = text.lower()
    high_words = ['burst', 'fire', 'danger', 'spark', 'short circuit', 'flood', 'leakage']
    medium_words = ['pothole', 'broken', 'overflow', 'blocked', 'stagnant', 'garbage']
    for w in high_words:
        if w in text:
            return 'HIGH'
    for w in medium_words:
        if w in text:
            return 'MEDIUM'
    return 'LOW'

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('complaint.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)", (name,email,password,'citizen'))
            conn.commit()
        except:
            pass
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('complaint.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            if user[4] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/citizen')
    return render_template('login.html')

@app.route('/citizen', methods=['GET','POST'])
def citizen():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        ctype = request.form['type']
        desc = request.form['description']
        area = request.form['area']
        landmark = request.form['landmark']
        urgency = get_urgency(desc)
        conn = sqlite3.connect('complaint.db')
        c = conn.cursor()
        c.execute("INSERT INTO complaints (user_id,type,description,area,landmark,urgency,status) VALUES (?,?,?,?,?,?,?)", (session['user_id'], ctype, desc, area, landmark, urgency, 'Pending'))
        conn.commit()
        conn.close()
    conn = sqlite3.connect('complaint.db')
    c = conn.cursor()
    c.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC", (session['user_id'],))
    complaints = c.fetchall()
    conn.close()
    return render_template('citizen_dashboard.html', complaints=complaints, name=session.get('name'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    conn = sqlite3.connect('complaint.db')
    c = conn.cursor()
    c.execute("UPDATE complaints SET status='Overdue' WHERE status='Pending' AND datetime(created_at) <= datetime('now', '-1 day')")
    conn.commit()
    c.execute("SELECT COUNT(*) FROM complaints")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'")
    inprogress = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM complaints WHERE status='Overdue'")
    overdue = c.fetchone()[0]
    c.execute("SELECT complaints.*, users.name FROM complaints JOIN users ON complaints.user_id = users.id ORDER BY CASE status WHEN 'Overdue' THEN 1 ELSE 2 END, CASE urgency WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END")
    complaints = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', complaints=complaints, total=total, pending=pending, inprogress=inprogress, resolved=resolved, overdue=overdue)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    conn = sqlite3.connect('complaint.db')
    c = conn.cursor()
    c.execute("SELECT urgency, COUNT(*) FROM complaints GROUP BY urgency")
    urgency_data = c.fetchall()
    c.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
    status_data = c.fetchall()
    c.execute("SELECT type, COUNT(*) FROM complaints GROUP BY type")
    type_data = c.fetchall()
    conn.close()
    return render_template('analytics.html', urgency_data=urgency_data, status_data=status_data, type_data=type_data)

@app.route('/update_status/<int:id>/<status>')
def update_status(id, status):
    if status == "InProgress":
        status = "In Progress"
    conn = sqlite3.connect('complaint.db')
    c = conn.cursor()
    c.execute("UPDATE complaints SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)