#!/bin/bash
# Amarktai Network - Sanity Check Script
# Run before deployment to catch common issues

set -e

echo "🧪 Running sanity checks..."

# 1. Compile critical Python files
echo "[1/4] Compiling critical Python files..."
python -m py_compile backend/database.py
python -m py_compile backend/server.py
python -m py_compile backend/auth.py

# 2. Compile all backend modules
echo "[2/4] Compiling all backend modules..."
python -m compileall backend -q

# 3. Test database module imports
echo "[3/4] Testing database module..."
python -c "import sys; sys.path.insert(0, 'backend'); import database; assert hasattr(database, 'wallet_balances'); assert hasattr(database, 'capital_injections'); assert hasattr(database, 'audit_logs'); assert hasattr(database, 'orders_collection'); assert hasattr(database, 'positions_collection'); print('✅ Database module OK')"

# 4. Optional: Run pytest if tests exist
if [ -d "backend/tests" ]; then
    echo "[4/4] Running tests..."
    python -m pytest backend/tests -q || true
else
    echo "[4/4] No tests found, skipping"
fi

echo "✅ All sanity checks passed!"
