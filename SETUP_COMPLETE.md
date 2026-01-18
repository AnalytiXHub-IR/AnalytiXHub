# 🚀 OPENCHAIN IR v4.0 - Quick Start Guide

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
