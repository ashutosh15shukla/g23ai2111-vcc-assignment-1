from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

if not os.path.exists('database'):
    os.makedirs('database')

def init_db():
    conn = sqlite3.connect('database/messages.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       sender TEXT NOT NULL,
                       recipient TEXT NOT NULL,
                       message TEXT NOT NULL,
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        expression = request.form.get('expression', '')
        result = ''
        try:
            result = str(eval(expression))
        except Exception as e:
            result = 'Error'
        return render_template('calculator.html', expression=expression, result=result)
    return render_template('calculator.html', expression='', result='')

@app.route('/dialer', methods=['GET', 'POST'])
def dialer():
    if request.method == 'POST':
        number = request.form.get('number', '')
        return render_template('dialer.html', number=number)
    return render_template('dialer.html', number='')

@app.route('/messages')
def messages():
    conn = sqlite3.connect('database/messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            CASE
                WHEN sender = 'Me' THEN recipient
                ELSE sender
            END as contact,
            MAX(timestamp) as last_timestamp
        FROM messages
        WHERE NOT (sender = 'Me' AND recipient = 'Me')
        GROUP BY contact
        ORDER BY last_timestamp DESC
    ''')
    threads = cursor.fetchall()

    thread_details = []
    for contact, last_timestamp in threads:
        cursor.execute('''
            SELECT message FROM messages
            WHERE (sender = ? OR recipient = ?)
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (contact, contact))
        last_message = cursor.fetchone()
        if last_message:
            thread_details.append((contact, last_timestamp, last_message[0]))

    conn.close()
    return render_template('threads.html', threads=thread_details)

@app.route('/messages/<recipient>', methods=['GET', 'POST'])
def thread_messages(recipient):
    if request.method == 'POST':
        message = request.form.get('message', '')
        conn = sqlite3.connect('database/messages.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender, recipient, message) VALUES ('Me', ?, ?)", (recipient, message))
        conn.commit()
        conn.close()
        return redirect(url_for('thread_messages', recipient=recipient))

    conn = sqlite3.connect('database/messages.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sender, recipient, message, timestamp FROM messages WHERE (recipient = ? OR sender = ?) AND NOT (sender = 'Me' AND recipient = 'Me') ORDER BY timestamp ASC", (recipient, recipient))
    messages = cursor.fetchall()
    conn.close()
    return render_template('messages.html', messages=messages, recipient=recipient)

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

app.run(host="0.0.0.0", port=5000, debug=True)