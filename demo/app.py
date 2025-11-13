from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_login import login_required, LoginManager, UserMixin, login_user, logout_user, current_user
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'  # For sessions and flash messages

# initialise flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# userClass for flask-login
class User(UserMixin):
    def __init__(self, id, username, hashed_password):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password

# load user from database
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, hashed_password FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(id=row['id'], username=row['username'], hashed_password=row['hashed_password'])
    return None

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
@login_required
def dashboard():
    '''if 'user_id' not in session:
        return redirect(url_for('login'))'''
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user from database (using parameterized query to avoid SQL injection)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, hashed_password FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['hashed_password'], password):
            session['user_id'] = user['id']
            login_user(User(id=user['id'], username=user['username'], hashed_password=user['hashed_password']))
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Registration logic
    # on POST, get form data and insert new user into database
    if request.method == 'POST':
        username = request.form['username']
        displayName = request.form['display_name']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirm_password']

        conn = get_db_connection()
        cursor = conn.cursor()

        if password != confirmPassword:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO Users (username, hashed_password, email, display_name) VALUES (?, ?, ?, ?)",
                (username, hashed_pw, email, displayName)
            )
            conn.commit()
            cursor.execute("SELECT id, username, hashed_password FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()

            # keep flask-login and session in sync
            login_user(User(id=user['id'], username=user['username'], hashed_password=user['hashed_password']))
            session['user_id'] = user['id']

            flash('Registration successful!', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
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
@login_required
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
            # Using parameterized query to avoid SQL injection
            cursor.execute(
                f"INSERT INTO ProgressLogs (user_id, date, title, details) VALUES (?, ?, ?, ?)",
                (session['user_id'], date, title, details)
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

    cursor.execute('SELECT * FROM ProgressLogs WHERE user_id = ? ORDER BY date DESC', (session["user_id"],))
    posts = cursor.fetchall()
    conn.close()
    # display no posts, if user has none 
    # display all posts if user has - dynamic
    return render_template('viewProgress.html', posts = posts)

if __name__ == '__main__':
    app.run(debug=True)