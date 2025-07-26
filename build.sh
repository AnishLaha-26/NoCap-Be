#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Apply database migrations if needed
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input

# Create cache directory if it doesn't exist
mkdir -p staticfiles

# Set proper permissions for the web server
chmod -R 755 staticfiles
