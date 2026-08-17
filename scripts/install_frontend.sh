#!/usr/bin/env bash
set -e
echo "Installing frontend dependencies..."
cd frontend
npm install --no-audit --no-fund
echo "Frontend dependencies installed successfully!"
