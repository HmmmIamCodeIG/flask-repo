from flask import Flask, render_template

app = Flask(__name__)

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

@appp.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
