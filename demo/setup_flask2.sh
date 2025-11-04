# ...existing code...
#!/usr/bin/env bash
set -e

echo "Enter the project name:"
read project_name

# Create project folder and enter it
mkdir -p "$project_name"
cd "$project_name" || exit 1

# Create templates and static folders
mkdir -p templates static

# Create virtual environment (try py -> python3 -> python)
if command -v py >/dev/null 2>&1; then
    py -3 -m venv venv
elif command -v python3 >/dev/null 2>&1; then
    python3 -m venv venv
else
    python -m venv venv
fi

# Install packages using the venv's pip (works on Windows and Unix)
if [ -f "venv/Scripts/pip.exe" ] || [ -f "venv/Scripts/pip" ]; then
    VENV_PIP="venv/Scripts/pip"
else
    VENV_PIP="venv/bin/pip"
fi

"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install flask flask_session

# create app.py that renders the template
cat > app.py << 'EOF'
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')
EOF

# create basic HTML template in templates folder
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hello from template</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <h1>Hello from template!</h1>
    <p>If you see this page, the template rendering works.</p>
</body>
</html>
EOF

# css setup
cat > static/styles.css <<'EOF'
body {
    color: #111;
    font-family: Arial, sans-serif;
    margin: 2rem;
}
EOF

# Echo instructions
echo ""
echo "setup complete! Your project '$project_name' is ready."
echo ""
echo "To activate the virtual environment (Windows PowerShell):"
echo "  cd $project_name"
echo "  .\\venv\\Scripts\\Activate.ps1"
echo ""
echo "To activate (Windows cmd.exe):"
echo "  cd $project_name"
echo "  .\\venv\\Scripts\\activate.bat"
echo ""
echo "To activate (WSL / macOS / Linux):"
echo "  cd $project_name"
echo "  source venv/bin/activate"
echo ""
echo "To run the app after activation:"
echo "  # Option A: using flask CLI"
echo "  # PowerShell:"
echo "  \$env:FLASK_APP = 'app.py'"
echo "  flask run"
echo ""
echo "  # cmd.exe:"
echo "  set FLASK_APP=app.py"
echo "  flask run"
echo ""
echo "  # bash / WSL:"
echo "  export FLASK_APP=app.py"
echo "  flask run"
echo ""
echo "  # Option B: run directly (no env vars needed):"
echo "  python app.py"
echo ""
echo "Then open http://127.0.0.1:5000/ in your browser."
# ...existing code...