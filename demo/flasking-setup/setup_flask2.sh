# Prompt for project name
echo "Enter the project name:"
read project_name

# Create project folder
mkdir "$project_name"
cd "$project_name"

# Create templates and static folders
mkdir template static

# Detect operating system
    py -m venv venv
    source venv/Scripts/activate

# install flask session
pip install flask flask_session
# create app.py with basic flask app
cat > app.py << EOF
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)
EOF

# create basic HTL template in templaes folder
cat > templates/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width-device-width, initial scale=1.0">
    <title>Hello World</title>
</head>
<body>
</body>
</html>
EOF

# css setup
cat > static/styles.css <<EOF
body {
    color: black;
    font-family: Arial, sans-serif;
}
EOF

# Echo instructions
echo ""
echo "setup complete! Your project '$project_name' is ready."
echo ""
echo "To reactivate the virtual environment after reopening the IDE:"
if [["$OSTYPE" == "darwin"* ]]; then
    echo "  cd $project_name"
    echo "  source venv/bin/activate"
else
    echo "  cd $project_name"
    echo "  venv//Scripts//activate"
fi
echo ""
echo "to run flask app:"
echo "flask run"
echo "then open http://122.0.0.1:5000/ in your browser."
