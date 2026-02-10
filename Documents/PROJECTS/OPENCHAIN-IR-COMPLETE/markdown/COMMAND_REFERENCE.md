# 🚀 OPENCHAIN IR v4.0 - Quick Command Reference

## Installation & Setup

### Step 1: Run Complete Setup
```powershell
python setup_complete.py
```
Automatically:
- ✓ Checks Python version
- ✓ Installs dependencies
- ✓ Sets up PostgreSQL database
- ✓ Creates .env file
- ✓ Initializes database tables
- ✓ Generates startup scripts

### Step 2: Configure APIs
```powershell
# Edit .env file
notepad .env

# Add your keys:
# ETHERSCAN_API_KEY=your_key_from_etherscan.io
# GOOGLE_API_KEY=your_gemini_api_key
```

### Step 3: Start Services (Terminal 1)
```powershell
# Start PostgreSQL
Start-Service -Name postgresql-x64-15

# Verify it's running
Get-Service postgresql-x64-15 | Select Status
```

### Step 4: Start Redis (Terminal 2)
```powershell
# Option A: If installed locally
redis-server

# Option B: Using Docker (recommended)
docker run -d -p 6379:6379 --name redis redis:latest
```

### Step 5: Start Flask App (Terminal 3)
```powershell
python app.py
```
Outputs:
```
* Running on http://127.0.0.1:5000
* Press CTRL+C to quit
```

### Step 6: Start Celery Worker (Terminal 4 - Optional)
```powershell
# For batch processing
celery -A app.celery worker --loglevel=info
```

---

## Daily Usage Commands

### View Web Interface
```
http://localhost:5000
```

### Analyze Single Address
```powershell
# Via web interface:
# 1. Click "Analyze Address"
# 2. Enter address: 0x...
# 3. Select chain: ethereum, polygon, bitcoin
# 4. Click Analyze

# Via Python console:
python -c "
from eth_live import fetch_eth_address_with_counts
txs, counts = fetch_eth_address_with_counts('0xaddress', 'api_key')
"
```

### Batch Analysis from CSV
```powershell
# Prepare CSV file with addresses column
# Upload via web interface -> "Batch Analysis"

# Or via Python:
python -c "
from batch_analyzer import BatchAnalyzer
batch = BatchAnalyzer()
results = batch.analyze_from_csv('addresses.csv')
"
```

### Enable Real-Time Monitoring
```powershell
# Via web interface:
# 1. Click "Monitoring"
# 2. Add address
# 3. Set alert settings
# 4. Enable monitoring

# Via Python:
python -c "
from real_time_monitor import RealTimeMonitor
monitor = RealTimeMonitor()
monitor.add_address('0xaddress')
monitor.start_monitoring()
"
```

### Check Smart Contract
```powershell
python -c "
from smart_contract_analyzer import SmartContractAnalyzer
analyzer = SmartContractAnalyzer('your_etherscan_key')
analysis = analyzer.analyze_contract('0xContractAddress')
print(analysis)
"
```

### Trace Fund Flow
```powershell
python -c "
from taint_analysis import TaintAnalyzer
analyzer = TaintAnalyzer(transactions)
traces = analyzer.trace_fund_flow('0xSourceAddress')
print(traces)
"
```

### Check Threat Intelligence
```powershell
python -c "
from threat_intelligence import ThreatIntelligenceAPI
ti = ThreatIntelligenceAPI()
result = ti.check_address('0xSuspiciousAddress')
print(result)
"
```

### Track DeFi Activity
```powershell
python -c "
from defi_analyzer import DeFiAnalyzer
analyzer = DeFiAnalyzer()
activity = analyzer.analyze_defi_activity('0xAddress')
print(activity)
"
```

---

## Database Management

### Connect to PostgreSQL
```powershell
# Using psql client
$env:PGPASSWORD='password'
psql -U openchain_user -d openchain_ir -h localhost
```

### Common SQL Queries
```sql
-- Count addresses in case
SELECT COUNT(*) FROM addresses WHERE case_id = 1;

-- List all alerts
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;

-- Find suspicious addresses
SELECT address, risk_score FROM addresses WHERE risk_score > 75 ORDER BY risk_score DESC;

-- Get all transactions for address
SELECT * FROM transactions WHERE from_address = '0x...' OR to_address = '0x...' ORDER BY timestamp DESC;

-- Check threat intel flags
SELECT * FROM threat_intel WHERE is_flagged = true;

-- Monitor active jobs
SELECT * FROM monitoring_jobs WHERE status = 'active';

-- Batch processing status
SELECT status, progress_percent, completed_count FROM batch_jobs ORDER BY started_at DESC;
```

### Backup Database
```powershell
# Create backup
$env:PGPASSWORD='password'
pg_dump -U openchain_user -d openchain_ir > backup.sql

# Restore from backup
psql -U openchain_user -d openchain_ir < backup.sql
```

### Reset Database (WARNING: Deletes all data)
```powershell
python -c "
from db_models import Base, engine

# Drop all tables
Base.metadata.drop_all(engine)

# Recreate all tables
Base.metadata.create_all(engine)

print('Database reset complete')
"
```

---

## Monitoring & Maintenance

### Check Services Status
```powershell
# PostgreSQL
Get-Service postgresql-x64-15 | Select Name, Status

# Redis
Get-Process redis-server -ErrorAction SilentlyContinue | Select ProcessName, Id

# Flask app
# Should be running in terminal window
```

### View Application Logs
```powershell
# Flask logs appear in terminal where app.py is running

# Celery logs
# Run celery worker with --loglevel=info to see logs

# PostgreSQL logs (Windows)
# C:\Program Files\PostgreSQL\15\data\log\
```

### Performance Monitoring
```powershell
# Check Redis memory usage
redis-cli INFO memory

# Check PostgreSQL connections
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Monitor API rate limits
# Check .env configuration:
# MAX_CONCURRENT_REQUESTS=5
# REQUEST_TIMEOUT=30
```

### Clear Cache
```powershell
# Clear Redis cache (WARNING: Affects all sessions/jobs)
redis-cli FLUSHDB

# Or clear specific pattern
redis-cli KEYS "pattern:*" | xargs redis-cli DEL
```

---

## Troubleshooting Commands

### Test Etherscan API
```powershell
python -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('ETHERSCAN_API_KEY')

response = requests.get(
    'https://api.etherscan.io/api',
    params={
        'module': 'account',
        'action': 'balance',
        'address': '0xd8da6bf26964af9d7eed9e03e53415d37aa96045',
        'apikey': key
    }
)

print(response.json())
"
```

### Test BlockScout API
```powershell
python -c "
import requests

response = requests.get(
    'https://eth.blockscout.com/api/v2/addresses/0xd8da6bf26964af9d7eed9e03e53415d37aa96045'
)

print(response.json())
"
```

### Test Database Connection
```powershell
python -c "
from db_models import SessionLocal

db = SessionLocal()
result = db.execute('SELECT 1')
print('✓ Database connection OK')
db.close()
"
```

### Test Redis Connection
```powershell
redis-cli ping
# Should output: PONG
```

### Test Gemini AI API
```powershell
python -c "
from gemini import generate_comprehensive_analysis

# Note: Requires valid API key in .env
result = generate_comprehensive_analysis({})
print(result)
"
```

### Check All Services
```powershell
# Create test script
Write-Host "Testing all services..." -ForegroundColor Green

# PostgreSQL
try {
    psql -U openchain_user -d openchain_ir -c "SELECT 1"
    Write-Host "✓ PostgreSQL: OK" -ForegroundColor Green
} catch {
    Write-Host "✗ PostgreSQL: FAILED" -ForegroundColor Red
}

# Redis
try {
    redis-cli ping
    Write-Host "✓ Redis: OK" -ForegroundColor Green
} catch {
    Write-Host "✗ Redis: FAILED" -ForegroundColor Red
}

# Python dependencies
python -c "
import flask, sqlalchemy, redis, celery
print('✓ Python packages: OK')
"
```

---

## Development Commands

### Run Unit Tests
```powershell
# If tests exist
python -m pytest tests/ -v

# Or specific test file
python -m pytest tests/test_analyzer.py -v
```

### Debug Mode
```powershell
# Set environment
$env:FLASK_ENV='development'
$env:FLASK_DEBUG='1'

# Run app
python app.py

# Now browser will auto-reload on code changes
```

### Profile Code Performance
```powershell
python -c "
import cProfile
import pstats
from analyzer import analyze_live_eth

# Profile a function
profiler = cProfile.Profile()
profiler.enable()

# Your code here...
result = analyze_live_eth([...], '0xaddress')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
"
```

### Update Requirements
```powershell
# Generate updated requirements
pip freeze > requirements.txt

# Or install additional package
pip install package_name
pip freeze >> requirements.txt
```

---

## Docker Commands (Alternative)

### Build Docker Image
```powershell
docker build -t openchain-ir:v4.0 .
```

### Run in Docker
```powershell
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/openchain_ir" \
  -e REDIS_URL="redis://redis:6379" \
  -e ETHERSCAN_API_KEY="your_key" \
  --name openchain \
  openchain-ir:v4.0
```

### Docker Compose (Full Stack)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://openchain:password@db:5432/openchain_ir
      REDIS_URL: redis://redis:6379
      ETHERSCAN_API_KEY: ${ETHERSCAN_API_KEY}
    
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: openchain_ir
      POSTGRES_USER: openchain
      POSTGRES_PASSWORD: password
    volumes:
      - pg_data:/var/lib/postgresql/data
    
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

volumes:
  pg_data:
```

Start with:
```powershell
docker-compose up -d
```

---

## Production Deployment

### Gunicorn (Production Server)
```powershell
# Install
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service (Linux)
```ini
[Unit]
Description=OPENCHAIN IR
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/openchain-ir
ExecStart=/usr/bin/gunicorn -w 4 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## Useful Shortcuts

| Command | Purpose |
|---------|---------|
| `python app.py` | Start Flask app |
| `celery -A app.celery worker` | Start Celery worker |
| `redis-cli` | Connect to Redis CLI |
| `psql -U openchain_user -d openchain_ir` | Connect to PostgreSQL |
| `pip install -r requirements.txt` | Install dependencies |
| `python -m pytest` | Run tests |
| `python setup_complete.py` | Complete setup |
| `python setup_db.py` | Initialize database |
| `python -c "code here"` | Run Python one-liner |

---

## Help & Documentation

| Resource | Location |
|----------|----------|
| Feature Guide | `FEATURE_IMPLEMENTATION_GUIDE.md` |
| Architecture | `SYSTEM_ARCHITECTURE.md` |
| Setup Complete | `SETUP_COMPLETE.md` |
| Quick Start | `QUICK_START.md` |
| Advanced Guide | `ADVANCED_FEATURES_GUIDE.md` |
| API Requirements | `api_requirements.md` |
| README | `README.md` |
| Implementation | `IMPLEMENTATION_COMPLETE_V4.md` |

---

## Emergency Commands

### Stop Everything
```powershell
# Stop Flask
# CTRL+C in Flask terminal

# Stop Celery
# CTRL+C in Celery terminal

# Stop Redis
redis-cli SHUTDOWN

# Stop PostgreSQL
Stop-Service -Name postgresql-x64-15
```

### Emergency Database Restore
```powershell
# If database is corrupted, restore from backup
psql -U postgres -d openchain_ir < backup.sql
```

### Clear All Cache
```powershell
# WARNING: Loses all cached data and jobs
redis-cli FLUSHALL
```

### Restart All Services
```powershell
# Stop services
Stop-Service -Name postgresql-x64-15
redis-cli SHUTDOWN

# Start services
Start-Service -Name postgresql-x64-15
redis-server
```

---

**Last Updated**: December 24, 2025  
**Version**: 4.0  
**Status**: ✅ Production Ready
