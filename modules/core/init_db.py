#!/usr/bin/env python3
"""
Initialize AnalytiXHub Database (PostgreSQL/SQLite)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env
load_dotenv()

def initialize():
    print("\n" + "="*70)
    print("  AnalytiXHub - Initializing Database")
    print("="*70)

    try:
        from sqlalchemy import create_engine, inspect
        # Try to get from .env or default to SQLite
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_url = 'sqlite:///openchain_ir.db'
            print(f"⚠️ DATABASE_URL not set in .env. Defaulting to: {db_url}")
        
        print(f"\n✓ Target Database: {db_url}")
        
        # Import models
        try:
            from modules.core.db_models import Base, engine as db_engine, init_db as run_init
            engine = db_engine
        except ImportError as e:
            print(f"✗ Failed to import db_models: {e}")
            # Fallback for direct script execution if needed
            from db_models import Base, engine as db_engine
            engine = db_engine

        print("✓ Engine connection established")
        
        # Create all tables defined in Base.metadata
        print("✓ Initializing tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables initialized")
        
        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ Tables found: {len(tables)}")
        for table in sorted(tables):
            print(f"   - {table}")
            
        # Optional: Run initial data population if needed
        # run_init() # This might populate chains etc.

        print("\n" + "="*70)
        print("  ✅ DATABASE READY")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    initialize()
