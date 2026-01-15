# 🧪 TEST CASES FOR WEB INTERFACE

## How to Test

1. Open http://127.0.0.1:5000 in your browser
2. Copy one of the test cases below
3. Fill in the form with the data
4. Click "Analyze"
5. View the results

---

## TEST CASE 1: Ethereum - Vitalik Buterin (Well-known address)

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** Ethereum
- **Date From:** 2025-11-01
- **Date To:** 2025-12-24
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ Should find 10,000+ transactions
- ✅ Low risk score (LOW)
- ✅ Entity: Vitalik Buterin
- ✅ Multiple victims/suspects

---

## TEST CASE 2: Polygon - Active Address

**Form Fields:**
- **Address:** `0xe5277AA484C6d11601932bfFE553A55E37dC04Cf`
- **Chain:** Polygon
- **Date From:** 2025-12-01
- **Date To:** 2025-12-24
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ Should find ~48 transactions
- ✅ Risk score: ~25 (MEDIUM)
- ✅ Shows Polygon in results
- ✅ Chain ID: 137

---

## TEST CASE 3: Arbitrum - Test Cross-Chain

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** Arbitrum
- **Date From:** (leave empty)
- **Date To:** (leave empty)
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ Should find 10,000+ transactions on Arbitrum
- ✅ Chain ID: 42161
- ✅ Different transaction counts than Ethereum
- ✅ Same address, different chain data

---

## TEST CASE 4: BSC - Chain Switching Test

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** BNB Smart Chain (BSC)
- **Date From:** (leave empty)
- **Date To:** (leave empty)
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ May show 0 transactions (address not active on BSC)
- ✅ No error - gracefully handles no data
- ✅ Chain ID: 56
- ✅ Risk score: LOW

---

## TEST CASE 5: Optimism - Low Activity Address

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** Optimism
- **Date From:** (leave empty)
- **Date To:** (leave empty)
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ May show 0 transactions
- ✅ Chain ID: 10
- ✅ No errors with empty results

---

## TEST CASE 6: Base - Newer Chain

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** Base
- **Date From:** (leave empty)
- **Date To:** (leave empty)
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ Chain ID: 8453
- ✅ Tests newer chain support
- ✅ Unified V2 endpoint works

---

## TEST CASE 7: Date Range Filter - Ethereum

**Form Fields:**
- **Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Chain:** Ethereum
- **Date From:** 2025-12-20
- **Date To:** 2025-12-24
- **Include Internal Txs:** ☐ (unchecked)
- **Include Token Transfers:** ☐ (unchecked)

**Expected Results:**
- ✅ Should find fewer transactions (recent only)
- ✅ Risk assessment based on recent activity
- ✅ Date range properly applied

---

## TEST CASE 8: Full Analysis - Polygon with All Options

**Form Fields:**
- **Address:** `0xe5277AA484C6d11601932bfFE553A55E37dC04Cf`
- **Chain:** Polygon
- **Date From:** 2025-01-01
- **Date To:** 2025-12-24
- **Include Internal Txs:** ☑ (checked)
- **Include Token Transfers:** ☑ (checked)

**Expected Results:**
- ✅ More comprehensive data
- ✅ Includes internal transactions
- ✅ Includes token transfers
- ✅ Complete risk assessment

---

## ✅ Expected Success Indicators

When you run these tests, you should see:

✅ **At the top of the page:**
- The address you entered
- The chain name (Ethereum, Polygon, etc.)
- Success message: "Analysis complete: X transactions analyzed on [chain]"

✅ **In the Results section:**
- Total transactions count
- Risk score (0-100)
- Confidence level (%)
- Entity type and information
- Top senders/receivers

✅ **In the Reports section:**
- PDF report generation works
- Timeline, Heatmap, Sankey visualizations available
- No errors or crashes

---

## 🐛 If You Get Errors

**"No transactions found"**
- The address may not have activity on that chain
- Try Test Case 1 (Vitalik on Ethereum) - guaranteed data

**"API Error"**
- Check if Etherscan API key is valid in `.env`
- Wait a moment and retry (rate limiting)

**"Chain not supported"**
- Make sure chain name matches exactly (lowercase)
- See list of 15 supported chains

---

## 📋 All 15 Supported Chains (for dropdown)

1. Ethereum
2. BNB Smart Chain (BSC)
3. Polygon
4. Optimism
5. Arbitrum One (Arbitrum)
6. Base
7. Avalanche C-Chain
8. Fantom (Opera)
9. Cronos
10. Moonbeam
11. Gnosis (xDai)
12. Celo
13. Blast
14. Linea
15. Sepolia (Testnet)

---

## 🎯 Quick Test Summary

| Test Case | Chain | Address | Expected Txs | Status |
|-----------|-------|---------|--------------|--------|
| 1 | Ethereum | Vitalik | 10,000+ | ✅ |
| 2 | Polygon | Test | ~48 | ✅ |
| 3 | Arbitrum | Vitalik | 10,000+ | ✅ |
| 4 | BSC | Vitalik | 0 | ✅ |
| 5 | Optimism | Vitalik | 0 | ✅ |
| 6 | Base | Vitalik | 0 | ✅ |
| 7 | Ethereum | Vitalik (date range) | 0-100 | ✅ |
| 8 | Polygon | Test (full) | ~48+ | ✅ |

**Start with Test Case 1 or 2 for guaranteed results!**

