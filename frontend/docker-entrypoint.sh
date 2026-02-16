#!/bin/sh
set -e

cd /app

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

echo "Starting Next.js dev server..."
exec npm run dev
