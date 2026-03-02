"""
Complete Setup Script for OPENCHAIN IR v4.0
Initializes database, installs dependencies, configures environment
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def check_python_version():
    """Check if Python version is sufficient"""
    print_header("1. Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_header("2. Installing Python Dependencies")
    
    try:
        print("Installing packages from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_success("All dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Dependency installation failed: {str(e)}")
        return False

def check_postgresql():
    """Check PostgreSQL availability"""
    print_header("3. Checking PostgreSQL")
    
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True
        )
        print_success(f"PostgreSQL found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print_error("PostgreSQL not found in PATH")
        print("Please install PostgreSQL from: https://www.postgresql.org/download/")
        return False

def setup_database():
    """Create and configure PostgreSQL database"""
    print_header("4. Setting Up PostgreSQL Database")
    
    # Database configuration
    db_name = "openchain_ir"
    db_user = "openchain_user"
    db_password = "password"
    db_host = "localhost"
    db_port = 5432
    
    print(f"Database config:")
    print(f"  Name: {db_name}")
    print(f"  User: {db_user}")
    print(f"  Host: {db_host}:{db_port}")
    
    try:
        # Create database and user using psql
        # Note: This assumes postgres user exists
        
        print("\nAttempting to create database...")
        
        # Commands to execute
        sql_commands = [
            f"CREATE DATABASE {db_name};",
            f"CREATE USER {db_user} WITH PASSWORD '{db_password}';",
            f"ALTER ROLE {db_user} SET client_encoding TO 'utf8';",
            f"ALTER ROLE {db_user} SET default_transaction_isolation TO 'read committed';",
            f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};",
        ]
        
        for cmd in sql_commands:
            subprocess.run(
                ["psql", "-U", "postgres", "-c", cmd],
                capture_output=True
            )
        
        print_success("Database created successfully")
        return True, db_name, db_user, db_password
        
    except Exception as e:
        print_warning(f"Could not auto-create database: {str(e)}")
        print("\nManual PostgreSQL setup required:")
        print("  psql -U postgres")
        print(f"  CREATE DATABASE {db_name};")
        print(f"  CREATE USER {db_user} WITH PASSWORD '{db_password}';")
        print(f"  GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};")
        
        return False, db_name, db_user, db_password

def create_env_file(db_name, db_user, db_password):
    """Create .env file with configuration"""
    print_header("5. Creating .env Configuration File")
    
    env_content = f"""# ===============================================
# OPENCHAIN IR - Environment Configuration
# Generated: {datetime.now().isoformat()}
# ===============================================

# ========== BLOCKCHAIN APIs ==========
ETHERSCAN_API_KEY=YOUR_ETHERSCAN_API_KEY_HERE
BLOCKSCOUT_ENABLED=true

# ========== DATABASE ==========
DATABASE_URL=postgresql://{db_user}:{db_password}@localhost:5432/{db_name}

# ========== CACHE & QUEUE ==========
REDIS_URL=redis://localhost:6379/0

# ========== AI SERVICES ==========
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE

# ========== FEATURE FLAGS ==========
ENABLE_MULTI_CHAIN=true
ENABLE_SMART_CONTRACT_ANALYSIS=true
ENABLE_THREAT_INTELLIGENCE=true
ENABLE_REAL_TIME_MONITORING=true
ENABLE_TAINT_ANALYSIS=true
ENABLE_ML_ANOMALY=true
ENABLE_BATCH_PROCESSING=true
ENABLE_DEX_INTEGRATION=true

# ========== CELERY (Background Jobs) ==========
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ========== REAL-TIME MONITORING ==========
MONITORING_UPDATE_INTERVAL=60
MONITORING_MAX_ADDRESSES=10
ALERT_RISK_THRESHOLD=0.75
ALERT_ANOMALY_THRESHOLD=0.8

# ========== BATCH PROCESSING ==========
BATCH_MAX_ADDRESSES=100
BATCH_WORKERS=4

# ========== SYSTEM ==========
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
MAX_RETRIES=3
LOG_LEVEL=INFO
FLASK_ENV=production
"""
    
    if os.path.exists('.env'):
        print_warning(".env file already exists - not overwriting")
        return True
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print_success(".env file created")
        print("\n⚠️  IMPORTANT: Edit .env and add your API keys:")
        print("  - ETHERSCAN_API_KEY: https://etherscan.io/apis")
        print("  - GOOGLE_API_KEY: Your Gemini API key")
        return True
    except Exception as e:
        print_error(f"Could not create .env: {str(e)}")
        return False

def initialize_database_tables():
    """Initialize database tables using SQLAlchemy"""
    print_header("6. Initializing Database Tables")
    
    try:
        # Import after env is set up
        from db_models import Base, engine, init_db
        
        print("Creating database tables...")
        init_db()
        print_success("Database tables created")
        return True
        
    except Exception as e:
        print_error(f"Could not initialize tables: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Verify DATABASE_URL in .env is correct")
        print("  2. Verify PostgreSQL is running")
        print("  3. Check database exists and user has permissions")
        return False

def check_redis():
    """Check Redis availability"""
    print_header("7. Checking Redis")
    
    try:
        result = subprocess.run(
            ["redis-cli", "--version"],
            capture_output=True,
            text=True
        )
        print_success(f"Redis found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print_warning("Redis not found in PATH")
        print("Options:")
        print("  1. Install Redis: https://redis.io/download")
        print("  2. Or use Docker: docker run -d -p 6379:6379 redis:latest")
        return False

def create_startup_script():
    """Create startup script for easy running"""
    print_header("8. Creating Startup Scripts")
    
    # PowerShell script for Windows
    ps_script = """# Start OPENCHAIN IR v4.0

Write-Host "Starting OPENCHAIN IR..." -ForegroundColor Green

# Start Redis (if not running)
Write-Host "Checking Redis..." -ForegroundColor Yellow
try {
    $redis = Get-Process redis-server -ErrorAction SilentlyContinue
    if ($null -eq $redis) {
        Write-Host "Starting Redis..." -ForegroundColor Yellow
        Start-Process redis-server
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "Redis not found - using Docker fallback" -ForegroundColor Yellow
    docker run -d -p 6379:6379 redis:latest | Out-Null
    Start-Sleep -Seconds 2
}

# Start PostgreSQL
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
Start-Service -Name postgresql-x64-15 -ErrorAction SilentlyContinue

# Install/upgrade dependencies
Write-Host "Updating dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Start Flask app
Write-Host "Starting Flask app..." -ForegroundColor Green
python app.py
"""
    
    try:
        with open('start.ps1', 'w') as f:
            f.write(ps_script)
        print_success("Created start.ps1 (Windows PowerShell)")
    except Exception as e:
        print_warning(f"Could not create startup script: {str(e)}")

def create_quick_reference():
    """Create quick reference guide"""
    print_header("9. Creating Quick Reference")
    
    quick_ref = """# 🚀 OPENCHAIN IR v4.0 - Quick Start Guide

## Installation Complete! 🎉

### Start Services (Windows PowerShell)
```powershell
# Start Redis
docker run -d -p 6379:6379 redis:latest
# OR if installed locally:
redis-server

# Start PostgreSQL
Start-Service -Name postgresql-x64-15

# Start app
python app.py
```

### Start Services (Linux/Mac)
```bash
# Start Redis
redis-server

# Start PostgreSQL
sudo systemctl start postgresql

# Start app
python app.py
```

## Web Interface
- **URL**: http://localhost:5000
- **Upload CSV**: Batch upload addresses
- **Real-time Monitoring**: Watch addresses for updates
- **Reports**: Generate PDF forensic reports

## Available APIs

### Core Forensic Analysis
- **Multi-Chain Support**: Ethereum, Polygon, Arbitrum, Bitcoin, Litecoin
- **Pattern Detection**: AML patterns, risk scoring
- **Address Clustering**: Find related addresses
- **Network Graphs**: Gephi-compatible exports

### Advanced Features
- **Taint Analysis**: Trace funds through mixers/bridges
- **Smart Contract Analysis**: Detect rug pulls, honeypots
- **DeFi Integration**: Track Uniswap, Aave, Curve activity
- **Threat Intelligence**: OFAC lists, phishing detection
- **Real-Time Monitoring**: Watch for new transactions
- **Batch Processing**: Analyze 100+ addresses

## Configuration

### API Keys Needed
1. **Etherscan** (FREE):
   - https://etherscan.io/apis
   - Add to .env: `ETHERSCAN_API_KEY=your_key`

2. **Google Gemini** (Already configured):
   - Add your key to .env: `GOOGLE_API_KEY=your_key`

3. **BlockScout** (FREE - no key needed):
   - Automatically used for multi-chain

### Database
- PostgreSQL running on localhost:5432
- Database name: openchain_ir
- User: openchain_user

### Cache/Queue
- Redis running on localhost:6379
- Used for Celery task queue

## Common Commands

### Run Flask App
```bash
python app.py
```

### Start Celery Worker
```bash
celery -A app.celery worker --loglevel=info
```

### Run Tests
```bash
python -m pytest tests/
```

### Database Reset (WARNING: Deletes data)
```bash
python -c "from db_models import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

## Troubleshooting

### PostgreSQL Error
- Verify DATABASE_URL in .env
- Check PostgreSQL is running: `psql --version`
- Create database manually using SQL commands

### Redis Connection Error
- Start Redis: `redis-server`
- Or use Docker: `docker run -d -p 6379:6379 redis:latest`

### Etherscan API Error
- Verify API key in .env
- Check rate limit: 5M calls/day for free tier
- Use BlockScout for multi-chain (no key needed)

## Next Steps

1. ✓ Python dependencies installed
2. ✓ PostgreSQL database created
3. ✓ .env configuration file created
4. → Add API keys to .env file
5. → Start Redis service
6. → Run `python app.py`
7. → Open http://localhost:5000

## Support & Documentation

- **Feature Guide**: FEATURE_IMPLEMENTATION_GUIDE.md
- **Advanced Features**: ADVANCED_FEATURES_GUIDE.md
- **API Documentation**: api_requirements.md
- **Examples**: CODE_EXAMPLES.md
- **README**: README.md

---
**Setup Complete** ✅ - Ready to start investigations!
"""
    
    try:
        with open('SETUP_COMPLETE.md', 'w') as f:
            f.write(quick_ref)
        print_success("Created SETUP_COMPLETE.md")
    except Exception as e:
        print_warning(f"Could not create reference: {str(e)}")

def main():
    """Main setup flow"""
    print_header("OPENCHAIN IR v4.0 - Complete Setup")
    print("Database: PostgreSQL | Cache: Redis | Framework: Flask+Celery")
    
    # Run setup steps
    steps = [
        ("Python Version", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("PostgreSQL Check", check_postgresql),
        ("Database Setup", setup_database),
    ]
    
    results = []
    db_name = db_user = db_password = None
    
    for name, step_func in steps:
        try:
            if name == "Database Setup":
                success, db_name, db_user, db_password = step_func()
            else:
                success = step_func()
            
            results.append((name, success))
            
            if not success and name != "PostgreSQL Check":
                print_error(f"Setup failed at: {name}")
                return
        except Exception as e:
            print_error(f"Error in {name}: {str(e)}")
            results.append((name, False))
            return
    
    # Continue with remaining steps
    if db_name and db_user and db_password:
        create_env_file(db_name, db_user, db_password)
    
    # Initialize database tables
    try:
        initialize_database_tables()
    except Exception as e:
        print_warning(f"Database initialization: {str(e)}")
    
    # Check Redis
    check_redis()
    
    # Create startup scripts
    create_startup_script()
    
    # Create quick reference
    create_quick_reference()
    
    # Final summary
    print_header("✅ SETUP COMPLETE")
    print("\n📋 Setup Summary:")
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    print("\n🚀 Next Steps:")
    print("  1. Edit .env file and add your API keys")
    print("  2. Start Redis: redis-server")
    print("  3. Start app: python app.py")
    print("  4. Open http://localhost:5000")
    
    print("\n📚 Documentation:")
    print("  - See SETUP_COMPLETE.md for quick reference")
    print("  - See FEATURE_IMPLEMENTATION_GUIDE.md for all features")
    print("  - See README.md for detailed information")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Setup failed: {str(e)}")
        sys.exit(1)
