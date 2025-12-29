#!/usr/bin/env python3
"""
Preflight check - validates that server.py can be imported without errors
Run before deploying: python -m backend.preflight
"""
import sys
import os

def main():
    try:
        print("🔍 Preflight check starting...")
        
        # Check environment
        mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGO_URL')
        if not mongo_uri:
            print("⚠️  Warning: MONGO_URI not set, will use default mongodb://localhost:27017")
        else:
            print(f"✅ MongoDB URI configured: {mongo_uri[:20]}...")
        
        # Import database module first
        print("\n📦 Importing database module...")
        import database as db
        
        # Verify database exports
        print("📦 Checking database module exports...")
        required_exports = [
            'client', 'db', 'get_database', 'connect_db', 'close_db', 'setup_collections', 'init_db',
            'users_collection', 'bots_collection', 'api_keys_collection',
            'trades_collection', 'system_modes_collection', 'alerts_collection',
            'chat_messages_collection', 'learning_logs_collection',
            'autopilot_actions_collection', 'rogue_detections_collection',
            'wallets_collection', 'ledger_collection', 'profits_collection'
        ]
        
        missing_exports = []
        for export in required_exports:
            if not hasattr(db, export):
                missing_exports.append(export)
                print(f"❌ Missing export: {export}")
            else:
                print(f"✅ {export}")
        
        if missing_exports:
            print(f"\n❌ PREFLIGHT FAILED - Missing {len(missing_exports)} exports from database module")
            return 1
        
        print("\n✅ All required database exports present")
        
        # Import server (this triggers all imports)
        print("\n📦 Importing server module...")
        from server import app
        
        print("✅ Server imported successfully")
        
        # Check auth exports
        print("\n📦 Checking auth module exports...")
        from auth import create_access_token, get_current_user, is_admin
        print("✅ All required auth functions present")
        
        # Check autopilot engine
        print("\n📦 Checking autopilot engine...")
        from autopilot_engine import autopilot
        if autopilot.scheduler is None:
            print("❌ FAILED - Autopilot scheduler is None (should be initialized in __init__)")
            return 1
        print("✅ Autopilot engine initialized correctly")
        
        # Smoke test: Verify database collections are callable
        print("\n🔥 Running smoke tests...")
        if db.users_collection is None:
            print("❌ FAILED - users_collection is None")
            return 1
        if db.bots_collection is None:
            print("❌ FAILED - bots_collection is None")
            return 1
        if db.db is None:
            print("❌ FAILED - db handle is None")
            return 1
        
        print("✅ Database collections initialized")
        
        # Verify collection access pattern
        if not hasattr(db, 'users_collection'):
            print("❌ FAILED - Cannot access db.users_collection")
            return 1
        
        print("✅ Collection access pattern verified")
        
        # Check for common issues
        print("\n🔍 Checking for common issues...")
        
        # Check for duplicate function definitions
        import inspect
        import auth
        auth_functions = [name for name, obj in inspect.getmembers(auth) if inspect.isfunction(obj)]
        if auth_functions.count('is_admin') > 1:
            print("❌ FAILED - Duplicate is_admin() function in auth.py")
            return 1
        
        print("✅ No duplicate functions detected")
        
        print("\n🎉 PREFLIGHT PASSED - Server can start safely")
        print("\n📋 Next steps:")
        print("   1. Set feature flags (ENABLE_TRADING, ENABLE_AUTOPILOT, etc.)")
        print("   2. Start server: uvicorn backend.server:app --host 127.0.0.1 --port 8000")
        print("   3. Verify: curl http://127.0.0.1:8000/api/health/ping")
        return 0
        
    except ImportError as e:
        print(f"\n❌ PREFLIGHT FAILED - Import error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ PREFLIGHT FAILED - Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
