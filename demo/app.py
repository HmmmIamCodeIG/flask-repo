from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random
from flask_login import login_required, LoginManager, UserMixin, login_user, logout_user, current_user
from datetime import date


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'  
# For sessions and flash messages

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
    # fetch user from database
    conn = get_db_connection()
    cursor = conn.cursor()
    # secure way using parameterised queries
    # fetch user from database using parameterised query to avoid SQL injection
    cursor.execute("SELECT id, username, hashed_password FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(id=row['id'], username=row['username'], hashed_password=row['hashed_password'])
    return None

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  
    # Allows accessing columns by name
    return conn

@app.route('/')
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

        # insecure way (vulnerable to SQL injection) for demonstration purposes only
        '''conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, username, password FROM Users WHERE username = '{username}'")
        user = cursor.fetchone()
        conn.close()'''
        # vulnerable to SQL injection as it directly inserts user input into the SQL quer

        # secure way using parameterised queries
        # fetch user from database using parameterised query to avoid SQL injection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, hashed_password FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # verify password
        if user and check_password_hash(user['hashed_password'], password):
            session['user_id'] = user['id']
            # keep flask-login and session in sync
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
    # keep flask-login and session in sync
    logout_user()
    # clear session
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
        
        # secure way using parameterised queries
        conn = get_db_connection()
        cursor = conn.cursor()

        if password != confirmPassword:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        try:       
            # secure way using parameterised queries
            # plaintext passwords are insecure
            hashed_pw = generate_password_hash(password)
            # inserted_password = password  
            cursor.execute(
                "INSERT INTO Users (username, hashed_password, email, display_name) VALUES (?, ?, ?, ?)",
                (username, hashed_pw, email, displayName)
            )
            conn.commit()
            cursor.execute("SELECT id, username, hashed_password FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()
            # insecure way (vulnerable to SQL injection) for demonstration purposes only
            '''cursor.execute(
                f"INSERT INTO Users (username, password, email, display_name) VALUES ('{username}', '{password}', '{email}', '{displayName}')"
            )'''
            # this is insecure as it directly inserts user input into the SQL query, allowing for SQL injection

            # keep flask-login and session in sync
            login_user(User(id=user['id'], username=user['username'], hashed_password=user['hashed_password']))
            session['user_id'] = user['id']

            # success
            flash('Registration successful!', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
        # username or email already exists
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        # other errors
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/add_progress', methods=['GET', 'POST'])
@login_required
def add_progress():
    if request.method == 'POST':
        date = request.form['date']
        title = request.form['title']
        details = request.form['details']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Using parameterised query to avoid SQL injection
            cursor.execute(
                f"INSERT INTO ProgressLogs (user_id, date, title, details) VALUES (?, ?, ?, ?)",
                (session['user_id'], date, title, details)
            )
            # insecure way (vulnerable to SQL injection) for demonstration purposes only
            '''cursor.execute(
                f"INSERT INTO ProgressLogs (user_id, date, title, details) VALUES ({session['user_id']}, '{date}', '{title}', '{details}')"
            )'''
            # this is insecure as it directly inserts user input into the SQL query, allowing for SQL injection
            conn.commit()
            flash('Progress log added successfully!', 'success')
            return redirect(url_for('dashboard'))  
        # incomplete form data
        except sqlite3.IntegrityError:
            conn.close()
            flash('Please enter a complete log.', 'error')
            return redirect(url_for('add_progress'))
        # other errors
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('add_progress'))
        
    return render_template('addProgress.html')

@app.route('/view_progress', methods=['GET', 'POST'])
@login_required
def view_progress():
    conn = get_db_connection()
    cursor = conn.cursor()

    # fetch all progress logs for the logged-in user
    cursor.execute('SELECT * FROM ProgressLogs WHERE user_id = ? ORDER BY date ASC', (session["user_id"],))
    posts = cursor.fetchall()
    conn.close()
    # display no posts, if user has none 
    # display all posts if user has - dynamic
    return render_template('viewProgress.html', posts = posts)

@app.route('/quizzes', methods=['GET', 'POST'])
@login_required
def quizzes():
    feedback = ''
    user_answers = []
    questions = []
    # user selects which quiz to take
    selected_quiz = request.form.get('quiz') if request.method == 'POST' else None
    try:
        if selected_quiz:
            # read quiz questions from selected file
            with open(f'{selected_quiz}_quizzes.txt', 'r') as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    # strip whitespace and ignore empty parts
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    question_text = parts[0] # first part is question
                    correct_answer = parts[1] # second part is correct answer
                    choices = parts[2:-1] # all parts except first, second and last are choices
                    # shuffle choices to randomise order
                    random.shuffle(choices)
                    questions.append({
                        "text": question_text,
                        "correct": correct_answer,
                        "choices": choices,
                    })
    # no quiz file found
    except FileNotFoundError:
        flash('no file found.', 'error')
    # other errors
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    # process submitted answers
    if request.method == 'POST':
        for i in range(len(questions)):
            # get user's answer for each question
            user_answers.append(request.form.get(f'question_{i}', '').strip())
        # calculate score of correct answers
        correct = sum(1 for i, q in enumerate(questions)
                        # check if user's answer matches the correct answer
                        if i < len(user_answers) and user_answers[i] == q['correct'])
        # provide back to user how they did
        feedback = f"You got {correct} correct out of {len(questions)}!"
    return render_template('quizzes.html',
                            feedback=feedback,
                            user_answers=user_answers,
                            questions=questions)

@app.route('/quizzesMenu', methods=['GET', 'POST'])
@login_required
def quizzesMenu():
    return render_template('quizzesMenu.html')

if __name__ == '__main__':
    app.run(debug=True)