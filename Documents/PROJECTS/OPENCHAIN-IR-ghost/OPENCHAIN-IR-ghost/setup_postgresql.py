"""
Database Setup Guide for OPENCHAIN IR v3.0
Windows PowerShell Instructions
"""

import subprocess
import sys
import os
from pathlib import Path

print("""
╔════════════════════════════════════════════════════════════════╗
║  OPENCHAIN IR v3.0 - PostgreSQL Setup for Windows              ║
╚════════════════════════════════════════════════════════════════╝
""")

# Step 1: Check if PostgreSQL is installed
print("\n📋 Step 1: Checking PostgreSQL Installation...")
print("-" * 60)

try:
    result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ PostgreSQL found: {result.stdout.strip()}")
    else:
        print("❌ PostgreSQL not found. Installing...")
        print("\n📥 Download PostgreSQL from: https://www.postgresql.org/download/windows/")
        print("   Choose options:")
        print("   - PostgreSQL Version: 15+ (latest recommended)")
        print("   - Port: 5432 (default)")
        print("   - Password: Set a strong password (remember it!)")
        sys.exit(1)
except FileNotFoundError:
    print("❌ PostgreSQL not found in system PATH")
    print("📥 Please download from: https://www.postgresql.org/download/windows/")
    sys.exit(1)

# Step 2: Create database and user
print("\n📋 Step 2: Creating Database & User...")
print("-" * 60)

commands = [
    "CREATE USER openchain WITH PASSWORD 'openchain_ir_v3';",
    "ALTER USER openchain CREATEDB;",
    "CREATE DATABASE openchain_ir OWNER openchain;",
    "GRANT ALL PRIVILEGES ON DATABASE openchain_ir TO openchain;",
]

for cmd in commands:
    print(f"  Running: {cmd}")

print("""
To execute these commands:

1. Open PowerShell as Administrator
2. Connect to PostgreSQL:
   psql -U postgres

3. Run these commands:
   CREATE USER openchain WITH PASSWORD 'openchain_ir_v3';
   ALTER USER openchain CREATEDB;
   CREATE DATABASE openchain_ir OWNER openchain;
   GRANT ALL PRIVILEGES ON DATABASE openchain_ir TO openchain;
   \\q (to exit)

4. Test connection:
   psql -U openchain -d openchain_ir -h localhost
""")

# Step 3: Update .env file
print("\n📋 Step 3: Configuring .env File...")
print("-" * 60)

env_file = Path('.env')
if env_file.exists():
    print(f"✅ .env already exists")
else:
    print("📝 Creating .env from template...")
    template_file = Path('.env.template')
    if template_file.exists():
        with open(template_file) as f:
            template_content = f.read()
        
        # Set default database URL
        env_content = template_content.replace(
            'DATABASE_URL=postgresql://postgres:password@localhost:5432/openchain_ir',
            'DATABASE_URL=postgresql://openchain:openchain_ir_v3@localhost:5432/openchain_ir'
        )
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env created with PostgreSQL configuration")
        print("\n⚠️  Update the following in .env:")
        print("  1. ETHERSCAN_API_KEY - Get from https://etherscan.io/apis")
        print("  2. GOOGLE_API_KEY - Get from https://makersuite.google.com/app/apikey")
        print("  3. DATABASE_URL - If you used different password")
        print("  4. REDIS_URL - Keep as is for local Redis")

# Step 4: Initialize database tables
print("\n📋 Step 4: Initializing Database Tables...")
print("-" * 60)

print("""
Run this in Python to initialize tables:

  python -c "from db_models import init_db; init_db()"

Or run:
  python db_models.py
""")

# Step 5: Optional - Redis setup
print("\n📋 Step 5: Redis Setup (Optional - for Real-time Monitoring)...")
print("-" * 60)

print("""
For Local Redis (Windows):

Option A: Using WSL2 (Recommended)
  1. Open PowerShell as Administrator
  2. wsl --install -d Ubuntu
  3. wsl
  4. sudo apt-get update && sudo apt-get install redis-server
  5. redis-server

Option B: Using Windows Package Manager
  1. winget install Redis.Redis
  2. In Administrator PowerShell: redis-server

Option C: Docker
  1. Install Docker Desktop
  2. docker run -d -p 6379:6379 redis:latest

For Cloud Redis:
  - Redis Cloud: https://redis.cloud (free tier available)
  - AWS ElastiCache: https://aws.amazon.com/elasticache/
""")

# Step 6: Python dependencies
print("\n📋 Step 6: Installing Python Dependencies...")
print("-" * 60)

print("Running: pip install -r requirements.txt")
print("\nThis will install:")
print("  - SQLAlchemy (ORM)")
print("  - psycopg2 (PostgreSQL driver)")
print("  - scikit-learn, numpy, xgboost (ML)")
print("  - celery, redis (Task queue)")
print("  - slither-analyzer (Smart contract analysis)")

# Step 7: Verify setup
print("\n📋 Step 7: Verifying Setup...")
print("-" * 60)

print("""
Run these commands to verify:

1. Test PostgreSQL connection:
   python -c "import psycopg2; psycopg2.connect('postgresql://openchain:openchain_ir_v3@localhost/openchain_ir'); print('✅ PostgreSQL OK')"

2. Test database models:
   python db_models.py

3. Test multi-chain fetcher:
   python multi_chain.py

4. Test advanced analysis:
   python advanced_analysis.py

5. Start Flask app:
   python app.py
""")

print("""
╔════════════════════════════════════════════════════════════════╗
║  Setup Complete! Follow the steps above to complete setup.      ║
╚════════════════════════════════════════════════════════════════╝

📚 Quick Start:
1. Install PostgreSQL from: https://www.postgresql.org/download/windows/
2. Create database using the commands in Step 2
3. Update .env with your API keys
4. Run: python db_models.py
5. Run: pip install -r requirements.txt
6. Run: python app.py
7. Open: http://localhost:5000

Need help? Check FEATURES_REQUIREMENTS.md
""")
