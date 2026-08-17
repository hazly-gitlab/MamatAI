#!/usr/bin/env bash
set -e
echo "Installing backend requirements..."
pip install --upgrade pip
pip install -r backend/requirements.txt
echo "All requirements installed successfully!"
