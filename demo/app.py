from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_required, LoginManager, UserMixin, current_user, login_user, logout_user
import sqlite3
import logging  # library for logging security events
import bleach  # library for sanitisation of data
from email_validator import validate_email, EmailNotValidError
from zxcvbn import zxcvbn  # password rules
from forms import RegistrationForm, LoginForm, AddProgressForm, QuoteForm # importing classes from forms file
from flask_wtf import FlaskForm  # library to allow use of wtforms
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField  # fields for forms
from wtforms.validators import DataRequired, Length, Email  # validati0on types within forms
from flask_wtf.csrf import CSRFProtect  # allowing CSRF protection
from contextlib import contextmanager
import yfinance as yf
import os
from dotenv import load_dotenv  # use more secure session key
from datetime import datetime
import plotly.express as px
import plotly.io as pio

#region init
app = Flask(__name__)
load_dotenv()  # loads .env file
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')  # For sessions and flash messages
if not app.config['SECRET_KEY']:
    raise ValueError("No FLASK_SECRET_KEY set in environment or .env file!")

# Enable CSRF Protection
csrf = CSRFProtect(app)

# Uploads folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create uploads folder if it doesn't exist

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to /login for unauthorized access
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username
#endregion

#region subroutines
# run user input to remove dangerous content
def clean_input(s: str, allow_html: bool = False) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()
    if allow_html:
        # Allow very limited formatting (adjust tags as needed)
        return bleach.clean(s, tags=['p', 'br', 'strong', 'em'], attributes={}, strip=True)
    else:
        # Remove all HTML
        return bleach.clean(s, tags=[], strip=True)
        
def clean_log_title(s: str) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()
    # Remove all HTML
    cleaned = bleach.clean(s, tags=[], strip=True)
    return cleaned[:100]

def clean_log_details(s: str) -> str:
    # Strip dangerous content. allow_html=False removes all tags.
    s = s.strip()    
    # Allow very limited formatting (adjust tags as needed)
    return bleach.clean(s, tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'u'], attributes={}, strip=True)

# check if email is a vaild address instead of just a@b.com
def validate_email_strict(email: str) -> tuple[bool, str]:
    try:
        validate_email(email, check_deliverability=False)
        return True, ""
    except EmailNotValidError as e:
        return False, str(e)
    
# implement password rules    
def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Password must be at least 10 characters"    
    result = zxcvbn(password)
    if result['score'] < 3:
        warning = result['feedback']['warning'] or "Password is too weak"
        suggestions = " ".join(result['feedback']['suggestions'])
        return False, f"{warning} {suggestions}".strip()   
    return True, "Strong password"

# Load user from database
@login_manager.user_loader
def load_user(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, username FROM Users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()  # get the first record from query result

        if user:
            # create instance of user class
            return User(id=user['id'], username=user['username'])
        return None

    except Exception as e:
        # Log the error in development, but don't expose it to user
        print(f"Error loading user {user_id}: {e}")  # Replace with proper logging later
        return None

# Database connection function
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    # to close the db after the processing is complete
    try:
        yield conn  # keep connection open while actively accessing db
    finally:  # when finished        
        conn.close()
    
# retreving info from the database
def get_stock_info(ticker: str):
    if not ticker or len(ticker.strip()) < 1:  # if ticker name is too short
        return None, None, "Please enter a valid ticker symbol"
    
    ticker = ticker.upper().strip()  # convert to uppercase, remove any unwanted spaces

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Current price -- get the first price found then exit loop
        current_price = None  # initialise current price
        for key in ['currentPrice', 'regularMarketPrice', 'price']:
            if info.get(key):
                current_price = info.get(key)
                break
        
        stock_data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName') or f"{ticker} Stock",
            'current_price': round(current_price, 2) if current_price else None,
            'previous_close': round(info.get('regularMarketPreviousClose', 0), 2),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency', 'USD'),
            'summary': info.get('longBusinessSummary'),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
            }

        # Get historical data for chart (last 3 months)
        hist = stock.history(period="3mo")
        chart_data = None

        if not hist.empty:
            chart_data = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'close': hist['Close'].round(2).tolist()
            }

        return stock_data, chart_data, None

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None, None, f"Failed to fetch data for {ticker}. Please try again."

#endregion

@app.route('/')
def index():
    # return 'Index page'
    return render_template('dashboard.html')

@app.route('/add_progress', methods=['GET', 'POST'])
@login_required
def add_progress():
    form = AddProgressForm()  # for prevention of CSRF

    if form.validate_on_submit():
        date_str = form.date.data.strftime('%Y-%m-%d')   # Convert date to string
        title = clean_log_title(form.title.data)  # input sanitisation
        details = clean_log_details(form.details.data)

        # Uploading images
        image_path = None  # initialising image_path
        if form.image.data and form.image.data.filename:
            file = form.image.data  # store image into variable
            print(f"DEBUG: File received - Filename: {file.filename}")
            print(f"DEBUG: File content type: {file.content_type}")

            filename = secure_filename(file.filename)  # run the filename through werkzeug
            unique_filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"  # adding metadata to file name
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)  # set the file path with the folder so the app knows where to store the file

            try:
                # upload file to the server
                file.save(file_path) 
                image_path = f"uploads/{unique_filename}" # variable containing the filename that will be inserted to the databasse which will be used to call the image from statics/upload
                print(f"DEBUG: Image successfully saved to: {file_path}")
                print(f"DEBUG: image_path saved in DB will be: {image_path}")
            except Exception as e:
                print(f"ERROR saving image: {e}")
                flash(f'Failed to save image: {str(e)}', 'warning')
        else:
            print("DEBUG: No image file was uploaded or filename was empty")

        # function to insert data into the SQL table
        try:
            with get_db_connection() as conn: #  Establish connection to the database
                cursor = conn.cursor() # creating a cursor to execute commands into the SQL database
                cursor.execute(
                    "INSERT INTO ProgressLogs (user_id, date, title, details, image_path) VALUES (?, ?, ?, ?, ?)",
                    (current_user.id, date_str, title, details, image_path)
                )
                conn.commit()

            flash('Progress log added successfully!', 'success')
            return redirect(url_for('view_progress'))

        except Exception as e:
            flash('An error occurred while saving your progress.', 'error')
            print(f"ERROR saving progress: {e}")
            import traceback
            traceback.print_exc()  # Print full traceback in console

    return render_template('addProgress.html', form=form, username=current_user.username)
      
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT cash_balance FROM UserBalances WHERE user_id = ?", (current_user.id,))
            balance_row = cursor.fetchone()
            cash_balance = float(balance_row['cash_balance']) if balance_row else 0.0

            cursor.execute("""
                SELECT ticker, shares, average_buy_price
                FROM Portfolio 
                WHERE user_id = ?
                ORDER BY ticker
            """, (current_user.id,))
            holdings = cursor.fetchall()

        # First pass: Calculate market values and total portfolio value
        enhanced_holdings = []
        portfolio_value = 0.0
        total_unrealized_pnl = 0.0
        total_cost_basis = 0.0

        for holding in holdings:
            ticker = holding['ticker']
            shares = holding['shares']
            avg_buy_price = holding['average_buy_price']

            stock_data, _, error = get_stock_info(ticker)
            current_price = stock_data['current_price'] if stock_data and not error else None

            if current_price:
                market_value = round(shares * current_price, 2)
                unrealized_pnl = round((current_price - avg_buy_price) * shares, 2)
                cost_basis = round(avg_buy_price * shares, 2)

                portfolio_value += market_value
                total_unrealized_pnl += unrealized_pnl
                total_cost_basis += cost_basis

                enhanced_holdings.append({
                    'ticker': ticker,
                    'shares': shares,
                    'avg_buy_price': round(avg_buy_price, 2),
                    'current_price': round(current_price, 2),
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percent': round(((current_price - avg_buy_price) / avg_buy_price * 100), 2) if avg_buy_price > 0 else 0,
                    'weight': 0  # placeholder
                })
            else:
                enhanced_holdings.append({
                    'ticker': ticker,
                    'shares': shares,
                    'avg_buy_price': round(avg_buy_price, 2),
                    'current_price': None,
                    'market_value': None,
                    'unrealized_pnl': None,
                    'pnl_percent': None,
                    'weight': 0
                })

        total_portfolio_value = round(cash_balance + portfolio_value, 2)
        overall_return = round(((portfolio_value - total_cost_basis) / total_cost_basis * 100),
                               2) if total_cost_basis > 0 else 0

        # Second pass: Calculate correct weights
        if portfolio_value > 0:
            for holding in enhanced_holdings:
                if holding['market_value']:
                    holding['weight'] = round((holding['market_value'] / portfolio_value) * 100, 1)

        # Prepare data for Plotly pie chart
        tickers_for_pie = [h['ticker'] for h in enhanced_holdings if h['market_value']]
        weights_for_pie = [h['weight'] for h in enhanced_holdings if h['market_value']]

        # Create Plotly Pie Chart
        # import plotly.express as px
        # import plotly.io as pio

        allocation_chart = ""
        if tickers_for_pie and weights_for_pie:
            fig = px.pie(
                names=tickers_for_pie,
                values=weights_for_pie,
                title="Asset Allocation by Market Value",
                hole=0.1
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=450, showlegend=True)
            allocation_chart = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        # Top Gainer and Top Loser
        top_gainer = max(enhanced_holdings, key=lambda x: x.get('unrealized_pnl') or -999999, default=None)
        top_loser = min(enhanced_holdings, key=lambda x: x.get('unrealized_pnl') or 999999, default=None)

        return render_template('dashboard.html',
                               cash_balance=round(cash_balance, 2),
                               portfolio_value=round(portfolio_value, 2),
                               total_portfolio_value=total_portfolio_value,
                               total_unrealized_pnl=round(total_unrealized_pnl, 2),
                               overall_return=overall_return,
                               total_invested=round(total_cost_basis, 2),
                               holdings=enhanced_holdings,
                               top_gainer=top_gainer,
                               top_loser=top_loser,
                               allocation_chart=allocation_chart)

    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard.', 'error')        
        return render_template(
                'dashboard.html',
                cash_balance=0,
                portfolio_value=0,
                total_portfolio_value=0,
                total_unrealized_pnl=0,
                overall_return=0,
                total_invested=0,
                holdings=[],
                top_gainer=None,
                top_loser=None,
                allocation_chart=""
            )
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # if user logged in, send to dashboard
        return redirect(url_for('dashboard'))
    
    form = LoginForm()  # reference to the login form class - creating a loginform object

    if form.validate_on_submit():  # run the following code if the data in it is valid
        username = form.username.data.strip()  # cleaning the username and storing it
        password = form.password.data

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # check if user exists - if so return id, username, hashed pw
                cursor.execute( 
                    "SELECT id, username, hashed_password FROM Users WHERE username = ?",
                    (username,)
                )
                user_row = cursor.fetchone()  # storing the first result

            # IF not null, and passwords match
            if user_row and check_password_hash(user_row['hashed_password'], password):
                user = User(id=user_row['id'], username=user_row['username'])
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')

        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    '''if 'user_id' not in session:
        flash('You need to be logged in to view this content.', 'error')
    else:'''
    # session.pop('user_id', None)
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))
    # add a link to base.html to run this route -- in the navbar

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()

    # clean the data inserted by the user to prevent malicious code being injected
    if form.validate_on_submit():
        username = clean_input(form.username.data)
        displayName = clean_input(form.displayName.data)
        email = clean_input(form.email.data)
        password = form.password.data

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor() # creating a cursor to execute commands on the databse
                hashed_password = generate_password_hash(password)

                # register user into the database
                cursor.execute(
                    """INSERT INTO Users (username, hashed_password, email, display_name)
                       VALUES (?, ?, ?, ?)""",
                    (username, hashed_password, email, displayName)
                )
                conn.commit()  # finalise data in table / save data from query

                # automatically log new user in
                cursor.execute("SELECT id, username FROM Users WHERE username = ?", (username,))
                user_row = cursor.fetchone()

            if user_row:
                new_user = User(id=user_row['id'], username=user_row['username'])
                login_user(new_user)
                flash('Registration successful! Welcome!', 'success')
                return redirect(url_for('dashboard'))

        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')

    return render_template('register.html', form=form)

@app.route('/view_progress', methods=['GET', 'POST'])
@login_required
def view_progress():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor() 
            cursor.execute(
                """SELECT id, date, title, details, image_path
                   FROM ProgressLogs
                   WHERE user_id = ?
                   ORDER BY date DESC, id DESC""",  # Newer entries first
                (current_user.id,)
            )
            posts = cursor.fetchall()

        return render_template('viewProgress.html', posts=posts, username=current_user.username)

    except Exception as e:
        flash('Error loading your progress logs.', 'error')
        print(f"Error loading progress: {e}")

@app.route('/quote_stock', methods=['GET', 'POST'])
@login_required
def quote_stock():
    form = QuoteForm() # initialise the form
    stock_data = None
    chart_data = None
    error = None
    tickerName = None
        
    # Check if the form has been submitted and passes all CSRF/validation checks
    if form.validate_on_submit():
        tickerName = request.form.get('tickerName', '').strip()

        if tickerName:
            stock_data, chart_data, error = get_stock_info(tickerName) # if valid, call ticker info
        else:
            error = "Please enter a stock ticker symbol (e.g. AAPL)" # trigger error message if no data is sent through

    return render_template('quote_stock.html', form=form, stock_data=stock_data, chart_data=chart_data, error=error, tickerName=tickerName, username=current_user.username)


@app.route('/buy_stock', methods=['POST'])
@login_required
def buy_stock():
    ticker = request.form.get('ticker', '').strip().upper()
    shares = request.form.get('shares', type=int)

    if not ticker or not shares or shares <= 0:
        flash('Invalid ticker or number of shares.', 'error')
        return redirect(url_for('quote_stock'))

    # Get current price
    stock_data, _, error = get_stock_info(ticker)
    if error or not stock_data or not stock_data['current_price']:
        flash('Could not fetch current price. Please try again.', 'error')
        return redirect(url_for('stock_quote'))

    price_per_share = stock_data['current_price']
    total_cost = round(price_per_share * shares, 2)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get user's current cash balance
            cursor.execute("SELECT cash_balance FROM UserBalances WHERE user_id = ?", (current_user.id,))
            balance_row = cursor.fetchone()
            current_balance = balance_row['cash_balance'] if balance_row else 0.0

            if current_balance < total_cost:
                flash(f'Insufficient funds! You need ${total_cost:,.2f} but only have ${current_balance:,.2f}', 'error')
                return redirect(url_for('quote_stock'))

            # Update cash balance
            new_balance = round(current_balance - total_cost, 2)
            cursor.execute(
                "UPDATE UserBalances SET cash_balance = ? WHERE user_id = ?",
                (new_balance, current_user.id)
            )

            # Update or insert into Portfolio
            cursor.execute("""
                INSERT INTO Portfolio (user_id, ticker, shares, average_buy_price)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, ticker) 
                DO UPDATE SET 
                    shares = shares + ?,
                    average_buy_price = ((average_buy_price * shares) + (? * ?)) / (shares + ?),
                    last_updated = CURRENT_TIMESTAMP
            """, (current_user.id, ticker, shares, price_per_share,
                  shares, price_per_share, shares, shares))

            # Record transaction
            cursor.execute("""
                INSERT INTO Transactions 
                (user_id, ticker, transaction_type, shares, price_per_share, total_amount)
                VALUES (?, ?, 'BUY', ?, ?, ?)
            """, (current_user.id, ticker, shares, price_per_share, total_cost))

            conn.commit()

        flash(f'Successfully bought {shares} shares of {ticker} for ${total_cost:,.2f}', 'success')
        return redirect(url_for('quote_stock', ticker=ticker))   # Stay on same ticker

    except Exception as e:
        flash('An error occurred while processing your purchase.', 'error')
        print(f"Buy error: {e}")
        return redirect(url_for('quote_stock'))

@app.route('/sell_stock', methods=['POST'])
@login_required
def sell_stock():
    ticker = request.form.get('ticker', '').strip().upper()
    shares_to_sell = request.form.get('shares', type=int)

    if not ticker or not shares_to_sell or shares_to_sell < 1:
        flash('Invalid ticker or number of shares.', 'error')
        return redirect(url_for('dashboard'))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get current holding
            cursor.execute("""
                SELECT shares, average_buy_price 
                FROM Portfolio 
                WHERE user_id = ? AND ticker = ?
            """, (current_user.id, ticker))
            holding = cursor.fetchone()

            if not holding or holding['shares'] < shares_to_sell:
                flash(f'You only own {holding["shares"] if holding else 0} shares of {ticker}. Cannot sell {shares_to_sell} shares.', 'error')
                return redirect(url_for('dashboard'))

            avg_buy_price = holding['average_buy_price']

            # Get current market price
            stock_data, _, error = get_stock_info(ticker)
            if error or not stock_data or not stock_data.get('current_price'):
                flash('Could not fetch current price. Please try again later.', 'error')
                return redirect(url_for('dashboard'))

            current_price = stock_data['current_price']
            total_proceeds = round(current_price * shares_to_sell, 2)

            # Update cash balance
            cursor.execute("SELECT cash_balance FROM UserBalances WHERE user_id = ?", (current_user.id,))
            balance_row = cursor.fetchone()
            current_balance = float(balance_row['cash_balance']) if balance_row else 0.0
            new_balance = round(current_balance + total_proceeds, 2)

            cursor.execute(
                "UPDATE UserBalances SET cash_balance = ? WHERE user_id = ?",
                (new_balance, current_user.id)
            )

            # Update portfolio
            remaining_shares = holding['shares'] - shares_to_sell
            if remaining_shares > 0:
                cursor.execute("""
                    UPDATE Portfolio 
                    SET shares = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE user_id = ? AND ticker = ?
                """, (remaining_shares, current_user.id, ticker))
            else:
                cursor.execute("DELETE FROM Portfolio WHERE user_id = ? AND ticker = ?",
                             (current_user.id, ticker))

            # Record transaction
            cursor.execute("""
                INSERT INTO Transactions 
                (user_id, ticker, transaction_type, shares, price_per_share, total_amount)
                VALUES (?, ?, 'SELL', ?, ?, ?)
            """, (current_user.id, ticker, shares_to_sell, current_price, total_proceeds))

            conn.commit()

        flash(f'Successfully sold {shares_to_sell} shares of {ticker} for ${total_proceeds:,.2f}', 'success')

    except Exception as e:
        flash('An error occurred while selling the stock.', 'error')
        print(f"Sell error: {e}")
        import traceback
        traceback.print_exc()

    return redirect(url_for('dashboard'))


@app.route('/transactions')
@login_required
def transactions():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT t.id,
                                  t.ticker,
                                  t.transaction_type,
                                  t.shares,
                                  t.price_per_share,
                                  t.total_amount,
                                  t.timestamp,
                                  t.user_id
                           FROM Transactions t
                           WHERE t.user_id = ?
                           ORDER BY t.timestamp DESC
                           """, (current_user.id,))

            transactions = cursor.fetchall()

        return render_template('transactions.html',
                               transactions=transactions,
                               username=current_user.username)

    except Exception as e:
        print(f"Transactions error: {e}")
        flash('Error loading transaction history.', 'error')
        return redirect(url_for('dashboard'))

"""
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

"""

if __name__ == '__main__':
    app.run(debug=True)