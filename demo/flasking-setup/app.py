from flask import Flask, render_template, request
from dbm import sqlite3

app = Flask(__name__)
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

    # insecure: plain text password comparison
    conn = get_db_connection()
    cursor = conn.cursor()

    # using parameterized queries to prevent SQL injection
    cursor.execute('SELECT * FROM users WHERE username = ? AND hashed_password = ?', (username, password))
    user = cursor.fetchone()


@app.route('/')
def index():
    # return Index 
    return render_template('index.html')

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register', methods=["POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        display_name = request.form['display_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
