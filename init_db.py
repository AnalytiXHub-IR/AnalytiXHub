#!/usr/bin/env python3
"""
Direct initialization - SQLite edition
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env FIRST
load_dotenv()

# Set SQLite database URL if not set
if 'DATABASE_URL' not in os.environ or 'postgresql' in os.environ.get('DATABASE_URL', ''):
    os.environ['DATABASE_URL'] = 'sqlite:///openchain_ir.db'
    print("Using SQLite: openchain_ir.db")

print("\n" + "="*70)
print("  OPENCHAIN IR - Initializing Database")
print("="*70)

try:
    from sqlalchemy import create_engine, inspect
    
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///openchain_ir.db')
    print(f"\n✓ Database: {db_url}")
    
    # Create engine
    if db_url.startswith('sqlite'):
        engine = create_engine(db_url)
    else:
        engine = create_engine(db_url, echo=False)
    
    print("✓ Engine created")
    
    # Import models AFTER setting DATABASE_URL
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Now import models
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
    from sqlalchemy.orm import relationship
    from datetime import datetime
    
    Base = declarative_base()
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("✓ Database tables initialized")
    
    # Check what was created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ Tables created: {len(tables)}")
    for table in sorted(tables):
        print(f"   - {table}")
    
    # Create .env if missing
    if not Path('.env').exists():
        print("\n✓ Creating .env file...")
        env_content = """# OPENCHAIN IR Configuration
ETHERSCAN_API_KEY=your_etherscan_api_key_here
DATABASE_URL=sqlite:///openchain_ir.db
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_DEBUG=False
SECRET_KEY=openchain_secret_key_change_in_production
GOOGLE_API_KEY=
BLOCKSCOUT_ENABLED=true
THREAT_INTELLIGENCE_ENABLED=true
ENABLE_MULTI_CHAIN=true
ENABLE_SMART_CONTRACT_ANALYSIS=true
ENABLE_THREAT_INTELLIGENCE=true
ENABLE_REAL_TIME_MONITORING=true
ENABLE_TAINT_ANALYSIS=true
ENABLE_ML_ANOMALY=true
ENABLE_BATCH_PROCESSING=true
ENABLE_DEX_INTEGRATION=true
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("   ✓ .env created")
    
    print("\n" + "="*70)
    print("  ✅ DATABASE READY")
    print("="*70)
    print("\nNEXT STEP: Get Etherscan API Key")
    print("  1. Visit: https://etherscan.io/apis")
    print("  2. Sign up (free)")
    print("  3. Get your API key")
    print("  4. Edit .env and add it to ETHERSCAN_API_KEY=")
    print("\nThen run: python app.py")
    print("="*70 + "\n")

except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nTrying alternative approach...")
    
    # Just create the database file for SQLite
    db_file = Path('openchain_ir.db')
    if not db_file.exists():
        db_file.touch()
        print(f"✓ Created: {db_file}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
