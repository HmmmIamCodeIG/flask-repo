#!/bin/bash

# Prompt for project name
echo "Enter the project name:"
read project_name

# Create the project folder
mkdir "$project_name"
cd "$project_name"

# Create templates and static folders
mkdir templates static

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    python3 -m venv venv
    source venv/bin/activate
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    py -m venv venv
    source venv/Scripts/activate
else
    echo "Unsupported OS. Please create and activate the virtual environment manually."
    exit 1
fi

# Install Flask and Flask-Session
pip install flask flask_session
# pip install flask_sqlalchemy

# Create app.py with basic Flask app
cat > app.py << EOF
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
EOF

# Create basic HTML template in templates folder
cat > templates/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<body>
</body>
</html>
EOF

# Create basic CSS in static folder
cat > static/styles.css << EOF
body {
    color: black;
    font-family: Arial, sans-serif;
}
EOF

# Deactivate the environment
# deactivate

# Echo instructions
echo ""
echo "Setup complete! Your project '$project_name' is ready."
echo ""
echo "To reactivate the virtual environment after reopening the IDE:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  cd $project_name"
    echo "  source venv/bin/activate"
else
    echo "  cd $project_name"
    echo "  venv\\Scripts\\activate"
fi
echo ""
echo "To run the Flask app:"
echo "flask run"
echo "Then open http://127.0.0.1:5000/ in your browser."