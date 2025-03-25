#!/bin/bash

echo "Starting Social Media Forensics Web Application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the Flask app
echo "Starting the web server at http://localhost:5000"
echo "Press Ctrl+C to stop the server"
python3 app.py 