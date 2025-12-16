#!/usr/bin/env bash
#
# build_frontend.sh
#
# This script installs Node dependencies and builds the production
# frontend bundle.  It attempts to use Yarn if a lockfile is present
# and falls back to npm.  A minimum Node version of 20 is required.

set -euo pipefail

PROJECT_ROOT=$(dirname "$(readlink -f "$0")")/..
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "⚛️ Building frontend in $FRONTEND_DIR"

# Ensure correct Node version (>=20)
NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
  echo "❌ Node v20 or higher is required.  Current version: $(node -v)"
  exit 1
fi

cd "$FRONTEND_DIR"

# Install dependencies using Yarn or npm
if [ -f yarn.lock ]; then
  echo "📦 Installing dependencies with Yarn..."
  yarn install --frozen-lockfile
else
  echo "📦 Installing dependencies with npm..."
  npm ci --legacy-peer-deps || npm install --legacy-peer-deps
fi

# Build the project
if [ -f yarn.lock ]; then
  yarn build
else
  npm run build
fi

echo "✅ Frontend build complete"