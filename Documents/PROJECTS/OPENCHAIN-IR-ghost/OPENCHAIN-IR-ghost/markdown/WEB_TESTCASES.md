# 🧪 Web Interface Test Cases

## Overview
Test the OpenChain IR forensic dashboard across 4 different EVM chains. Each test case includes a real address, expected data patterns, and verification steps.

---

## TEST CASE 1: ETHEREUM - Vitalik Buterin (Known Entity)

**Chain:** Ethereum  
**Purpose:** Test known entity recognition and large transaction volume analysis

### Test Address
```
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

### Steps
1. Open http://127.0.0.1:5000
2. Select **Chain:** "ethereum"
3. Paste address: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
4. Leave dates empty (all-time analysis)
5. Check: Include Internal Txs ✓
6. Check: Include Token Transfers ✓
7. Click **ANALYZE**

### Expected Results (Overview Tab)

| Field | Expected Value | Status |
|-------|---|---|
| **Chain** | ETHEREUM (ID: 1) | ✅ |
| **Total Transactions** | ~10,000+ | ✅ |
| **Normal Txs** | 10,000+ | ✅ |
| **Entity Recognition** | "Vitalik Buterin" | ✅ |
| **Risk Score** | 90+ (High activity) | ✅ |
| **Unique Senders** | 6,000+ | ✅ |
| **Unique Receivers** | 200+ | ✅ |
| **Total Inflow** | 14,000+ ETH | ✅ |
| **Total Outflow** | 80,000+ ETH | ✅ |

### Verification Checklist
- [ ] Page loads without errors
- [ ] Overview tab shows all metrics
- [ ] Entity identified as "Vitalik Buterin"
- [ ] Charts tab renders correctly
- [ ] Timeline visualization loads
- [ ] At least 5 top suspects identified
- [ ] Risk factors detected
- [ ] Report generation button available

---

## TEST CASE 2: POLYGON - Active DeFi Address

**Chain:** Polygon  
**Purpose:** Test cross-chain support and moderate transaction volume

### Test Address
```
0xe5277AA484C6d11601932bfFE553A55E37dC04Cf
```

### Steps
1. Open http://127.0.0.1:5000
2. Select **Chain:** "polygon"
3. Paste address: `0xe5277AA484C6d11601932bfFE553A55E37dC04Cf`
4. **Date From:** `2025-11-01`
5. **Date To:** `2025-12-24`
6. Check: Include Internal Txs ✗ (unchecked)
7. Check: Include Token Transfers ✓
8. Click **ANALYZE**

### Expected Results (Overview Tab)

| Field | Expected Value | Status |
|-------|---|---|
| **Chain** | POLYGON (ID: 137) | ✅ |
| **Total Transactions** | 40-50 | ✅ |
| **Analysis Period** | 2025-11-01 to 2025-12-24 | ✅ |
| **Risk Score** | 20-40 (Low-Medium) | ✅ |
| **Net Flow** | Small (near zero) | ✅ |
| **Unique Senders** | 8-12 | ✅ |
| **Unique Receivers** | 12-18 | ✅ |

### Verification Checklist
- [ ] Chain correctly shows "POLYGON (ID: 137)"
- [ ] Date filter applied (Nov 1 - Dec 24)
- [ ] Fewer transactions than Ethereum (40-50 vs 10,000+)
- [ ] Token transfers included in count
- [ ] Risk score is lower (20-40)
- [ ] Overview metrics visible
- [ ] Evidence tab shows transaction list
- [ ] No errors in console

---

## TEST CASE 3: ARBITRUM - DEX Activity

**Chain:** Arbitrum  
**Purpose:** Test L2 chain support and identify DeFi patterns

### Test Address
```
0x1111111111111111111111111111111111111111
```

### Steps
1. Open http://127.0.0.1:5000
2. Select **Chain:** "arbitrum"
3. Paste address: `0x1111111111111111111111111111111111111111`
4. Leave dates empty
5. Check: Include Internal Txs ✓
6. Check: Include Token Transfers ✓
7. Click **ANALYZE**

### Expected Results (Overview Tab)

| Field | Expected Value | Status |
|-------|---|---|
| **Chain** | ARBITRUM (ID: 42161) | ✅ |
| **Entity Recognition** | DEX or Aggregator | ✅ |
| **Risk Score** | 50-70 (Medium) | ✅ |
| **Transaction Count** | 1,000+ | ✅ |
| **Pattern Detection** | High frequency trading | ✅ |

### Verification Checklist
- [ ] Chain correctly shows "ARBITRUM (ID: 42161)"
- [ ] Address resolves correctly
- [ ] Transaction data loads
- [ ] Heatmap shows activity patterns
- [ ] Sankey diagram renders
- [ ] Top suspects identified
- [ ] Risk factors listed
- [ ] Performance acceptable (< 15 sec load)

---

## TEST CASE 4: OPTIMISM - Low Activity Address

**Chain:** Optimism  
**Purpose:** Test L2 chain with minimal activity and edge cases

### Test Address
```
0x2222222222222222222222222222222222222222
```

### Steps
1. Open http://127.0.0.1:5000
2. Select **Chain:** "optimism"
3. Paste address: `0x2222222222222222222222222222222222222222`
4. **Date From:** `2025-12-01`
5. **Date To:** `2025-12-24`
6. Check: Include Internal Txs ✗ (unchecked)
7. Check: Include Token Transfers ✗ (unchecked)
8. Click **ANALYZE**

### Expected Results (Overview Tab)

| Field | Expected Value | Status |
|-------|---|---|
| **Chain** | OPTIMISM (ID: 10) | ✅ |
| **Total Transactions** | 0-10 (minimal) | ✅ |
| **Risk Score** | <20 (Very Low) | ✅ |
| **Unique Senders/Receivers** | 0-5 | ✅ |
| **Entity Type** | Unknown/New Account | ✅ |

### Verification Checklist
- [ ] Chain correctly shows "OPTIMISM (ID: 10)"
- [ ] Handles low/zero transaction count gracefully
- [ ] No errors with minimal data
- [ ] Overview shows "No suspicious patterns"
- [ ] Charts render with limited data
- [ ] UI doesn't break with edge case
- [ ] Error handling works correctly

---

## Quick Reference: All Test Addresses

| # | Chain | Address | Type | Purpose |
|---|-------|---------|------|---------|
| 1 | Ethereum | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | Known Entity | High volume |
| 2 | Polygon | `0xe5277AA484C6d11601932bfFE553A55E37dC04Cf` | Active | Medium volume |
| 3 | Arbitrum | `0x1111111111111111111111111111111111111111` | Aggregator | DEX pattern |
| 4 | Optimism | `0x2222222222222222222222222222222222222222` | Unknown | Low volume |

---

## Testing Workflow

### Phase 1: Individual Chain Tests
✅ Run each test case in order  
✅ Verify Overview tab loads for each  
✅ Check that chain IDs are correct  
✅ Ensure transaction counts match expectations

### Phase 2: Cross-Tab Verification
For **each test case**, verify these tabs:
- [ ] **1. Overview** - Summary statistics
- [ ] **2. Charts** - Entity distribution pie chart
- [ ] **🕸️ Clustering** - Address relationship graphs
- [ ] **🚨 Threat Intel** - Known threat flags
- [ ] **🤖 Anomalies** - ML-detected anomalies
- [ ] **3. Evidence** - Transaction list
- [ ] **4. Report** - Generate PDF report

### Phase 3: Feature Tests
For at least 2 test cases, verify:
- [ ] **Date Filtering** - Limits transactions to date range
- [ ] **Internal Txs** - Toggle changes transaction count
- [ ] **Token Transfers** - Toggle changes transaction type breakdown
- [ ] **Report Generation** - PDF downloads successfully
- [ ] **Network Graph** - Downloadable GEXF format
- [ ] **Performance** - All pages load in < 20 seconds

---

## Expected Common Results

### Overview Tab (All Tests)
```
✅ Chain badge with ID
✅ Transaction count badge  
✅ "Live Blockchain Data" indicator
✅ Normal/Internal/Token TX breakdown
✅ Total Inflow + Outflow values
✅ Net Flow calculation
✅ Risk indicators
```

### Evidence Tab (All Tests)
```
✅ Transaction table with columns:
   - From Address
   - To Address  
   - Value (ETH)
   - Timestamp
   - Status (Success/Failed)
✅ Sortable columns
✅ Scrollable for large datasets
```

### Report Tab (All Tests)
```
✅ "Generate Report" button
✅ Downloads PDF file
✅ PDF contains analysis summary
✅ Includes transaction data
✅ Shows risk assessment
✅ Lists detected patterns
```

---

## Success Criteria

### ✅ All Tests Pass When:
1. All 4 chains load without errors
2. Each test shows correct chain ID
3. Transaction counts are reasonable (0+ range)
4. No exceptions in browser console
5. All tabs render without blank sections
6. Report generation works
7. Data matches blockchain reality

### ⚠️ Known Issues to Ignore:
- Anomaly detection warning (ML library compatibility)
- Threat intelligence may be empty (address not flagged)
- Some addresses may have 0 transactions (expected)

---

## Performance Benchmarks

| Operation | Expected Time | Actual |
|-----------|---|---|
| Page load | < 2 sec | |
| Form submit (Ethereum) | 5-10 sec | |
| Form submit (Polygon) | 3-5 sec | |
| Form submit (Arbitrum) | 4-6 sec | |
| Report generation | 5-15 sec | |
| Chart rendering | < 1 sec | |

---

## Notes

- **Address Format:** All addresses must be 42 chars (0x + 40 hex digits)
- **Chain IDs:** Ethereum=1, Polygon=137, Arbitrum=42161, Optimism=10
- **Date Format:** YYYY-MM-DD only
- **Rate Limiting:** API has 0.25s delay between requests
- **First Run:** May take 10-15 sec to fetch and analyze

---

**Test Date:** December 24, 2025  
**Tested By:** [Your Name]  
**Result:** ⏳ Pending
