from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'  # For sessions and flash messages

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

@app.route('/')
def index():
    # return 'Index page'
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Insecure: Plain-text password comparison
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                f"SELECT * FROM Users WHERE username = '{username}' AND hashed_password = '{password}"
            )
            conn.commit()
            flash('Login successful!', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
        except:
            return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        displayName = request.form['displayName']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        # Insecure: Plain-text password comparison
        conn = get_db_connection()
        cursor = conn.cursor()

        # Using parameterized query to avoid SQL injection, but password is still plain-text
        # exists = cursor.execute(f"SELECT COUNT(username) FROM Users WHERE username = '{username}'")

        if password != confirmPassword:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        try:
            cursor.execute(
                f"INSERT INTO Users (username, hashed_password, email, display_name) VALUES ('{username}', '{password}', '{email}', '{displayName}')"
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)