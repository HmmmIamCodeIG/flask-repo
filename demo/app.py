from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import date

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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Insecure: Plain-text password comparison
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, hashed_password FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['hashed_password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' not in session:
        flash("you need to log in first.", 'error')
    else:
        session.pop('user_id', None)
        flash('You have been logged out.', 'success')
    return redirect(url_for('login'))
# add a link to base.html to run route -- in the navbar


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        displayName = request.form['display_name']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirm_password']

        # Insecure: Plain-text password comparison
        conn = get_db_connection()
        cursor = conn.cursor()

        # Using parameterized query to avoid SQL injection, but password is still plain-text
        # exists = cursor.execute(f"SELECT COUNT(username) FROM Users WHERE username = '{username}'"

        if password != confirmPassword:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        try:
            cursor.execute(
                f"INSERT INTO Users (username, hashed_password, email, display_name) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password) , email, displayName)
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

@app.route('/add_progress', methods=['GET', 'POST'])
def add_progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        date = request.form['date']
        title = request.form['title']
        details = request.form['details']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insecure: Directly interpolate session user_id into SQL for teaching purposes
            cursor.execute(
                f"INSERT INTO ProgressLogs (user_id, date, title, details) VALUES ('{session['user_id']}', '{date}', '{title}', '{details}')"
            )
            conn.commit()
            flash('Progress log added successfully!', 'success')
            return redirect(url_for('dashboard'))  # Redirect after successful insert
        except sqlite3.IntegrityError:
            conn.close()
            flash('Please enter a complete log.', 'error')
            return redirect(url_for('add_progress'))
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('add_progress'))
        
    return render_template('addProgress.html')

@app.route('/view_progress', methods=['GET', 'POST'])
def view_progress():
    if 'user_id' not in session:
        flash("Please log in to view your progress.", 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM ProgressLogs WHERE user_id = {session["user_id"]} ORDER BY date DESC')
    posts = cursor.fetchall()
    conn.close()
    # display no posts, if user has none 
    # display all posts if user has - dynamic
    return render_template('viewProgress.html', posts = posts)

if __name__ == '__main__':
    app.run(debug=True)