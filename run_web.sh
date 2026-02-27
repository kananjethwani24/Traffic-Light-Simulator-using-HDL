#!/bin/bash
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
python3 -m pip install -r web/requirements.txt

# Open Brave Browser in background after server starts
(sleep 2 && open -a "Brave Browser" http://127.0.0.1:5001) &

# Run the app
python3 web/app.py
