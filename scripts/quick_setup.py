#!/usr/bin/env python3
"""
Quick Setup for OPENCHAIN IR - SQLite Edition
No PostgreSQL or Docker required - Just run and go!
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_sqlite():
    """Setup SQLite database"""
    print("\n" + "="*70)
    print("  OPENCHAIN IR - Quick Setup (SQLite Edition)")
    print("="*70)
    
    # Create .env if not exists
    env_file = Path(".env")
    if not env_file.exists():
        print("\n✓ Creating .env file...")
        env_content = """# OPENCHAIN IR Configuration - SQLite Edition
ETHERSCAN_API_KEY=your_etherscan_api_key_here
DATABASE_URL=sqlite:///openchain_ir.db
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_DEBUG=False
SECRET_KEY=change_this_in_production_12345
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
MONITORING_UPDATE_INTERVAL=60
MONITORING_MAX_ADDRESSES=10
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
BATCH_MAX_ADDRESSES=100
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("   ✓ .env created")
    else:
        print("\n✓ .env already exists")
    
    # Initialize database
    print("\n✓ Initializing SQLite database...")
    try:
        from db_models import Base, engine
        Base.metadata.create_all(engine)
        print("   ✓ Database tables created")
    except Exception as e:
        print(f"   ✗ Error creating tables: {e}")
        return False
    
    # Create startup script
    print("\n✓ Creating startup script...")
    startup_script = """@echo off
cd /d "%~dp0"
echo ========================================
echo Starting OPENCHAIN IR v4.0
echo ========================================
echo.
echo API Key Setup:
echo   1. Get Etherscan API key: https://etherscan.io/apis
echo   2. Edit .env and add your key
echo.
echo Starting Flask server...
python app.py
pause
"""
    
    with open("start.bat", "w") as f:
        f.write(startup_script)
    print("   ✓ start.bat created")
    
    print("\n" + "="*70)
    print("  ✅ SETUP COMPLETE")
    print("="*70)
    print("\nNEXT STEPS:")
    print("  1. Edit .env and add Etherscan API key (ETHERSCAN_API_KEY)")
    print("  2. Run: python app.py")
    print("  3. Open: http://localhost:5000")
    print("\nFor Etherscan API key:")
    print("  → Go to https://etherscan.io/apis")
    print("  → Sign up (free)")
    print("  → Create API key")
    print("  → Paste in .env")
    print("\n" + "="*70)
    
    return True

if __name__ == "__main__":
    try:
        success = setup_sqlite()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)
