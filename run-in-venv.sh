#!/usr/bin/env bash
# run-in-venv.sh
# POSIX / Git-Bash friendly runner: creates venv if missing, activates it, installs requirements, runs main.py

set -euo pipefail

# If no venv, create one
if [ ! -d "venv" ]; then
  python -m venv venv
fi

# Try POSIX activate first (typical on Linux/macOS)
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  # Git-Bash on Windows
  . venv/Scripts/activate
else
  echo "Warning: no activate script found; virtualenv may not be activated"
fi

# Install requirements if provided
if [ -s requirements.txt ]; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
fi

# Execute the main script
python main.py "$@"
