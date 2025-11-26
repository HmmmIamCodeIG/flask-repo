from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random, os, re
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

### AUTHENTICATION ROUTES ###

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''if current_user.is_authenticated:
        return redirect(url_for('dashboard'))'''
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
            # insecure way (vulnerable to SQL injection) for demonstration purposes only
            '''cursor.execute(
                f"INSERT INTO Users (username, password, email, display_name) VALUES ('{username}', '{password}', '{email}', '{displayName}')"
            )'''
            
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

### PROGRESS LOG ROUTES ###

@app.route('/add_progress', methods=['GET', 'POST'])
@login_required
def add_progress():
    # on POST, get form data and insert new progress log into database
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

@app.route('/')
@login_required
def dashboard():
    '''if 'user_id' not in session:
        return redirect(url_for('login'))'''
    return render_template('dashboard.html')

### main quiz routes ###
@app.route('/quizzes', methods=['GET', 'POST'])
@login_required
def quizzes():
    # variables to store quiz data
    feedback = ''
    user_answers = []
    questions = []
    quiz_id = request.args.get('quiz_id')
    selected_quiz = request.form.get('quiz') or request.args.get('quiz')

    # custom quiz from database
    if quiz_id:
        # fetch quiz questions from database
        conn = get_db_connection()
        cursor = conn.cursor()
        # parameterised query to avoid SQL injection
        cursor.execute("SELECT question, choice1, choice2, choice3, choice4, correct_index FROM Questions WHERE quiz_id = ?", (quiz_id,))
        quiz_questions = cursor.fetchall()
        # if no questions exist for this quiz, show a message and redirect to the list
        if not quiz_questions:
            conn.close()
            flash('This quiz has no questions yet. Please add questions or pick another quiz.', 'error')
            return redirect(url_for('quizzesmenu'))
        # structure quiz questions
        for q in quiz_questions:
            choices = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
            correct_choice = choices[q['correct_index']]
            questions.append({
                "text": q['question'],
                "correct": correct_choice,
                "choices": choices,
            })
        # fetch quiz title
        cursor.execute("SELECT title FROM Quizzes WHERE id = ?", (quiz_id,))
        row = cursor.fetchone()
        quiz_title = row['title'] if row else 'Quiz'
        conn.close()

    # File-based quiz
    elif selected_quiz:
        # open corresponding quiz file
        with open(f'{selected_quiz}_quizzes.txt', 'r') as f:
            for raw in f:
                # process each line
                line = raw.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',') if p.strip()]
                question_text = parts[0]
                correct_answer = parts[1]
                choices = parts[2:-1]
                # shuffle choices
                random.shuffle(choices)
                questions.append({
                    "text": question_text,
                    "correct": correct_answer,
                    "choices": choices,
                })
        # set quiz title
        quiz_title = selected_quiz

    # Handle POST
    if request.method == 'POST':
        num_questions = len(questions)
        # gather user answers
        for i in range(num_questions):
            user_answers.append(request.form.get(f'question_{i}', '').strip())
        # calculate score
        correct = sum(1 for i, q in enumerate(questions)
                        if i < num_questions and user_answers[i] == q['correct'])
        feedback = f"You got {correct} correct out of {num_questions}!"
        # Store results in database
        storequizresults(current_user.id, quiz_title, correct, num_questions)

    # Render quiz template
    return render_template('quizzes.html',
                            feedback=feedback,
                            user_answers=user_answers,
                            questions=questions)

@app.route('/quizzesmenu', methods=['GET', 'POST'])
@login_required
def quizzesmenu():
    # File-based quizzes
    quiz_files = [f for f in os.listdir('.') if f.endswith('_quizzes.txt')] # list quiz files
    quiz_options = [f.replace('_quizzes.txt', '') for f in quiz_files] # extract quiz names

    # Custom quizzes from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    # fetch all custom quizzes
    cursor.execute("SELECT id, title, description, numQuestions FROM Quizzes ORDER BY id DESC")
    quizzes = cursor.fetchall()
    conn.close()
    # Handle quiz selection
    if request.method == 'POST':
        quiz_id = request.form.get('quiz_id')
        quiz_file_name = request.form.get('quiz')
        # If starting a custom quiz
        if quiz_id:
            return redirect(url_for('quizzes', quiz_id=quiz_id))
        # If starting a file-based quiz
        if quiz_file_name:
            return redirect(url_for('quizzes', quiz=quiz_file_name))

    return render_template('quizzesmenu.html', quiz_options=quiz_options, quizzes=quizzes)

@app.route('/viewquizresults', methods=['GET'])
@login_required
def viewquizresults():
    conn = get_db_connection()
    cursor = conn.cursor()
    # fetch all quiz results for the logged-in user
    cursor.execute(
        "SELECT quiz_title, score, num_questions, taken_at FROM UserQuizzes WHERE user_id = ? ORDER BY taken_at DESC",
        (current_user.id,)
    )
    quiz_results = cursor.fetchall()
    conn.close()
    return render_template('quizzesResults.html', quiz_results=quiz_results)

### FLASHCARD ROUTES
@app.route('/createflash', methods=['GET', 'POST'])
@login_required
def createflash():
    if request.method == 'POST':
        # variable to store flashcard set name, questions and answers
        flashcard_set_name = request.form['flashcard_set_name']
        questions = request.form.getlist('questions[]')
        answers = request.form.getlist('answers[]')
        created_at = date.today().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        # insert each flashcard into the database
        try:
            for question, answer in zip(questions, answers):
                cursor.execute(
                    "INSERT INTO Flashcards (user_id, flashcard_set, question, answer, created_at) VALUES (?, ?, ?, ?, ?)",
                    (current_user.id, flashcard_set_name, question, answer, created_at)
                )
            conn.commit()
            flash('Flashcard set created successfully!', 'success')
            return redirect(url_for('viewflash'))
        # error handling    
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('createflash.html')

@app.route('/viewflash', methods=['GET'])
@login_required
def viewflash():
    conn = get_db_connection()
    cursor = conn.cursor()
    # fetch all flashcards for the logged-in user 
    cursor.execute(
        "SELECT flashcard_set, question, answer FROM Flashcards WHERE user_id = ? ORDER BY created_at DESC",
        (current_user.id,)
    )
    # fetch all flashcards 
    flashcards = cursor.fetchall()
    conn.close()

    # Group flashcards by set name
    flashcard_sets = {}
    for card in flashcards:
        set_name = card['flashcard_set']
        # if not in a dictionary, add it
        if set_name not in flashcard_sets:
            flashcard_sets[set_name] = []
        # append list of flashcards to the set
        flashcard_sets[set_name].append({
            'question': card['question'],
            'answer': card['answer']
        })

    return render_template('viewflash.html', flashcard_sets=flashcard_sets)

def storequizresults(user_id, quiz_title, score, num_questions):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Insert quiz result directly
    cursor.execute(
        "INSERT INTO UserQuizzes (user_id, quiz_title, score, num_questions, taken_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, quiz_title, score, num_questions, date.today().isoformat())
    )
    # 
    conn.commit()
    conn.close()

### CUSTOM QUIZ CREATION ROUTES ###
@app.route('/quizsetup', methods=['GET', 'POST'])
@login_required
def quizsetup():
    if request.method == 'GET':
        # fetch existing quizzes to display
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, numQuestions FROM Quizzes ORDER BY id DESC")
        quizzes = cursor.fetchall()
        conn.close()
        return render_template('quizzesCreateSetupPage.html', quizzes=quizzes)

    # Handle quiz creation on POST
    title = request.form.get('title')
    description = request.form.get('description')
    numQuestions = request.form.get('numQuestions')
    # validate inputs
    try:
        numQuestions = int(numQuestions)
    # error converting to int
    except (TypeError, ValueError):
        flash('Number of questions must be a valid number.', 'error')
        return redirect(url_for('quizsetup'))
    if not title or not description or numQuestions <= 0:
        flash('Please fill in all fields with valid values.', 'error')
        return redirect(url_for('quizsetup'))

    # insert new quiz into database
    conn = get_db_connection()
    cursor = conn.cursor()
    # use parameterised query to avoid SQL injection
    try:
        cursor.execute(
            "INSERT INTO Quizzes (title, description, numQuestions) VALUES (?, ?, ?)",
            (title, description, numQuestions)
        )
        quiz_id = cursor.lastrowid
        conn.commit()
        session['created_quiz_id'] = quiz_id
        return redirect(url_for('questionsCustomSetup'))
    # error handling
    except sqlite3.IntegrityError:
        flash('Invalid entry. Please fill in all fields.', 'error')
        return redirect(url_for('quizsetup'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('quizsetup'))
    finally:
        conn.close()

@app.route('/questionsCustomSetup', methods=['GET', 'POST'])
@login_required
def questionsCustomSetup():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine quiz_id from POST, then query string, then session
    quiz_id = None
    if request.method == 'POST':
        quiz_id = request.form.get('quiz_id')
    # If not in POST, check query string or session
    if not quiz_id:
        quiz_id = request.args.get('quiz_id') or session.get('created_quiz_id') 
    try:
        quiz_id = int(quiz_id)
    except (TypeError, ValueError):
        conn.close()
        flash('No quiz found to add questions. Please create a quiz first.', 'error')
        return redirect(url_for('quizsetup'))
    
    # fetch quiz details
    cursor.execute("SELECT id, title, numQuestions FROM Quizzes WHERE id = ?", (quiz_id,))
    quiz_data = cursor.fetchone()

    # if no quiz found, redirect to quiz setup
    if not quiz_data:
        conn.close()
        flash('No quiz found to add questions. Please create a quiz first.', 'error')
        return redirect(url_for('quizsetup'))
    # Handle question submission
    if request.method == 'POST':
        # process submitted questions
        num_questions = quiz_data['numQuestions']
        for i in range(num_questions):
            # question and choices from form
            question = request.form.get(f'question_{i}')
            choices = [request.form.get(f'choice_{i}_{j}') for j in range(4)]
            correct_index_raw = request.form.get(f'correct_{i}')
            # if any field is missing
            if correct_index_raw is None:
                conn.close()
                flash(f'Please select a correct choice for question {i+1}.', 'error')
                return redirect(url_for('questionsCustomSetup', quiz_id=quiz_id))
            # validate correct index
            try:
                correct_index = int(correct_index_raw)
                # If radios post 1-4, convert to 0-3
                if correct_index not in (0, 1, 2, 3):
                    correct_index = correct_index - 1
                # error if out of range
                if correct_index not in (0, 1, 2, 3):
                    raise ValueError('correct_index out of range')
            # error converting to int
            except Exception:
                conn.close()
                flash(f'Invalid correct choice index for question {i+1}.', 'error')
                return redirect(url_for('questionsCustomSetup', quiz_id=quiz_id))
            # if any field is missing
            if not question or not all(choices):
                # flash error and redirect
                conn.close()
                flash(f'Please fill out all fields for question {i+1}.', 'error')
                return redirect(url_for('questionsCustomSetup', quiz_id=quiz_id))
            # insert question into database
            # use parameterised query to avoid SQL injection
            cursor.execute(
                "INSERT INTO Questions (quiz_id, question, choice1, choice2, choice3, choice4, correct_index) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (quiz_id, question, choices[0], choices[1], choices[2], choices[3], correct_index)
            )
    
        # commit changes to database
        conn.commit()
        conn.close()
        session.pop('created_quiz_id', None)
        flash('Questions successfully created!', 'success')
        return redirect(url_for('quizzesmenu'))

    conn.close()
    return render_template('questionsCustomSetup.html', quiz_data=quiz_data)

@app.route('/select_quiz', methods=['GET'])
@login_required
def select_quiz():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, numQuestions FROM Quizzes ORDER BY id DESC")
    quizzes = cursor.fetchall()
    conn.close()
    return render_template('customQuizzespages.html', quizzes=quizzes)

@app.route('/sdlc')
@login_required
def sdlc():
    return render_template('SDLC.html')

@app.route('/delete_quiz', methods=['POST'])
@login_required
def delete_quiz():
    quiz_id_raw = request.form.get('quiz_id')
    if not quiz_id_raw:
        flash('Please select a quiz to delete.', 'error')
        return redirect(url_for('select_quiz'))
    try:
        quiz_id = int(quiz_id_raw)
    except (TypeError, ValueError):
        flash('Invalid quiz ID.', 'error')
        return redirect(url_for('select_quiz'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Quizzes WHERE id = ?", (quiz_id,))
    cursor.execute("DELETE FROM Questions WHERE quiz_id = ?", (quiz_id,))
    conn.commit()
    conn.close()
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('select_quiz'))


if __name__ == '__main__':
    app.run(debug=True)