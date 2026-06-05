from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)
DB_PATH = "complaint.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT NOT NULL,
        department TEXT NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending',
        assigned_to TEXT,
        remarks TEXT,
        filed_date TEXT DEFAULT (date('now')),
        resolved_date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT,
        phone TEXT
    )''')
    c.execute("SELECT COUNT(*) as c FROM staff")
    if c.fetchone()['c'] == 0:
        conn.executemany('INSERT INTO staff (name,department,email,phone) VALUES (?,?,?,?)', [
            ('Rajesh Kumar', 'IT', 'rajesh@org.com', '9000000001'),
            ('Priya Nair', 'Admin', 'priya@org.com', '9000000002'),
            ('Suresh Das', 'Maintenance', 'suresh@org.com', '9000000003'),
            ('Anita Singh', 'HR', 'anita@org.com', '9000000004'),
        ])
    conn.commit(); conn.close()
    print("Complaint DB ready!")

@app.route('/complaints', methods=['GET'])
def get_complaints():
    conn = get_db()
    rows = conn.execute('SELECT * FROM complaints ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/complaints', methods=['POST'])
def add_complaint():
    d = request.json
    try:
        conn = get_db()
        conn.execute('''INSERT INTO complaints
            (complaint_no,name,email,phone,department,category,subject,description,priority,status,assigned_to)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (d['complaint_no'], d['name'], d.get('email',''), d['phone'],
             d['department'], d['category'], d['subject'], d['description'],
             d.get('priority','Medium'), d.get('status','Pending'), d.get('assigned_to','')))
        conn.commit(); conn.close()
        return jsonify({"message": "Complaint filed!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/complaints/<int:cid>', methods=['PATCH'])
def update_complaint(cid):
    d = request.json
    conn = get_db()
    fields = []
    values = []
    for key in ['status','assigned_to','remarks','priority']:
        if key in d:
            fields.append(f'{key}=?')
            values.append(d[key])
    if 'status' in d and d['status'] == 'Resolved':
        fields.append('resolved_date=date("now")')
    values.append(cid)
    conn.execute(f'UPDATE complaints SET {", ".join(fields)} WHERE id=?', values)
    conn.commit(); conn.close()
    return jsonify({"message": "Updated!"})

@app.route('/complaints/<int:cid>', methods=['DELETE'])
def delete_complaint(cid):
    conn = get_db()
    conn.execute('DELETE FROM complaints WHERE id=?', (cid,))
    conn.commit(); conn.close()
    return jsonify({"message": "Deleted!"})

@app.route('/staff', methods=['GET'])
def get_staff():
    conn = get_db()
    rows = conn.execute('SELECT * FROM staff ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/staff', methods=['POST'])
def add_staff():
    d = request.json
    conn = get_db()
    conn.execute('INSERT INTO staff (name,department,email,phone) VALUES (?,?,?,?)',
        (d['name'], d['department'], d.get('email',''), d.get('phone','')))
    conn.commit(); conn.close()
    return jsonify({"message": "Staff added!"}), 201

@app.route('/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as c FROM complaints').fetchone()['c']
    pending = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status='Pending'").fetchone()['c']
    in_progress = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status='In Progress'").fetchone()['c']
    resolved = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status='Resolved'").fetchone()['c']
    high = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE priority='High'").fetchone()['c']
    conn.close()
    return jsonify({"total": total, "pending": pending, "in_progress": in_progress, "resolved": resolved, "high_priority": high})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
