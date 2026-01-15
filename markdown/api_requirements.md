# Blockchain API Requirements & Free Sources

## Current Status

### ✅ NO KEY NEEDED (Free, Public APIs):
1. **BlockScout** (Ethereum & other chains)
   - No API key required
   - Public endpoint: `https://eth.blockscout.com/api/v2/`
   - Rate limit: Reasonable for testing
   - Status: ✅ TESTED & WORKS

2. **Mempool.space** (Bitcoin)
   - No API key required
   - But seems to have routing issues (404/400 on some endpoints)
   - Status: ⚠️ Partially working

### 🔑 FREE API KEYS (Quick Registration):

1. **Etherscan** (Ethereum)
   - ✅ You already have: `TUWDXD7G5R3KE7K3UN1YD5F7RKKJIGXDEY`
   - Issue: Key appears inactive/rate limited (returning NOTOK)
   - **Solution**: Re-register new key at https://etherscan.io/apis
   - Free tier: 5 calls/sec, 1M calls/day
   - Time to get: 2 minutes

2. **Blockchair** (Bitcoin, Litecoin, Dogecoin, all chains)
   - Requires FREE API key
   - Get at: https://blockchair.com/api/
   - Register with email → instant key
   - Free tier: 1M requests/month (~33k/day)
   - Time to get: 2 minutes
   - Status: ❌ Currently failing - need new key

3. **XRP Ledger** (XRP)
   - Has free PUBLIC nodes (no key needed)
   - Try: `https://xrpl.ws` (Wietse's public node)
   - Status: 🔄 Need to test properly

4. **BlockScout APIs** (Multiple chains)
   - Free endpoints available
   - Ethereum: `https://eth.blockscout.com/api/`
   - Status: ✅ Works

5. **CoinGecko** (Price data, optional for enrichment)
   - Free public API, no key required
   - Get at: https://www.coingecko.com/api
   - Status: Optional but useful

## Quick Setup Plan

### IMMEDIATE (Do these first):
1. Get new **Etherscan API key** (2 min)
   - Go to: https://etherscan.io/apis
   - Sign up → Create new API key
   - Add to .env file

2. Get new **Blockchair API key** (2 min)
   - Go to: https://blockchair.com/api/
   - Sign up → Copy your key
   - Add to .env file

3. Test **XRP Ledger** public node (no key needed)

### OPTIONAL (If you want more features):
- CoinGecko API (free, no registration needed for basic use)
- Add your API keys to .env

## .env File Template
```
ETHERSCAN_API_KEY=<get from etherscan.io/apis>
BLOCKCHAIR_API_KEY=<get from blockchair.com/api>
GEMINI_API_KEY=AIzaSyCBt2dPPFh8BUlN6_QTr4lSMax2bJhV97o
FLASK_ENV=development
```

## Summary
You need **2 free API keys** (5 minutes total):
1. Etherscan (for Ethereum) 
2. Blockchair (for Bitcoin, Litecoin, Dogecoin)

XRP and price data are optional (free public endpoints available).
