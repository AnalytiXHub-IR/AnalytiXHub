# OPENCHAIN IR - Quick Start Guide

## 🎯 What Your Tool Now Does

Your tool is now a **comprehensive cryptocurrency forensic analysis platform** that combines:
1. **Blockchain data analysis** (via Etherscan)
2. **Pattern detection** (AML/money laundering indicators)
3. **Risk scoring** (automated threat assessment)
4. **AI-powered insights** (via Google Gemini)
5. **Professional reporting** (PDF with charts and analysis)

---

## 📋 Complete Feature List

### Input:
- ✅ Ethereum address
- ✅ Date range (optional, defaults to all-time)

### Automatic Analysis:
- ✅ **Transaction metrics**: Total inflow/outflow, net flow, counts
- ✅ **Pattern detection**: 7 different suspicious patterns
- ✅ **Risk scoring**: 0-100 risk level with justification
- ✅ **Address tracking**: Top victims and suspects by volume
- ✅ **Network mapping**: Gephi-compatible graph export
- ✅ **Statistical analysis**: Average, median, max transactions
- ✅ **AI analysis**: Comprehensive narrative from Gemini

### Report Output:
- ✅ Executive summary with key metrics
- ✅ Transaction flow visualization (pie chart)
- ✅ Risk gauge chart
- ✅ Address distribution charts (top 5 in/out)
- ✅ Pattern analysis section
- ✅ Risk assessment with factors
- ✅ Complete victim list (top 10 by volume)
- ✅ Complete suspect list (top 10 by volume)
- ✅ Cash-out alerts
- ✅ AI forensic narrative
- ✅ Professional formatting (5+ pages, PDF)

---

## 🔍 Detected Patterns (Automatic)

### AML Red Flags:
1. **Rapid Succession**: Txs within 1-minute intervals → Structuring
2. **Mixing Service**: Many inputs, few outputs → Fund mixing
3. **Consolidation**: Small inputs → Large single output → Laundering prep
4. **Layering**: Complex multi-hop transactions → Obfuscation
5. **Dust Transfers**: <0.01 ETH amounts → Address verification/obfuscation
6. **High Frequency**: >50 transactions → Suspicious volume
7. **Round Amounts**: Exact ETH amounts → Coordinated activity

### Risk Contribution:
- Each pattern adds to total risk score
- Risk factors are documented in report
- Professional AML terminology used throughout

---

## 📊 How Risk Scoring Works

```
Risk Score Calculation:
├─ Rapid Succession     → +20 points
├─ High Frequency       → +15 points
├─ Mixing Service       → +25 points
├─ Consolidation        → +20 points
├─ Layering            → +18 points
├─ Dust Transactions   → +15 points (if >5)
├─ Round Amounts       → +10 points (if >30%)
└─ Total: Capped at 100

Risk Levels:
🟢 LOW:      0-30 points
🟡 MEDIUM:   31-50 points
🟠 HIGH:     51-70 points
🔴 CRITICAL: 71-100 points
```

---

## 👥 Victim vs Suspect Classification

### Victims:
- Addresses **sending funds TO** your target
- "Victims" = Inbound sources
- Tracked by total volume received
- Top 10 listed in report

### Suspects:
- Addresses **receiving funds FROM** your target
- "Suspects" = Outbound destinations
- Tracked by total volume sent
- Top 10 listed in report

### Why This Naming?
In forensic investigation:
- **Victims**: Sources of funds (if it's a theft)
- **Suspects**: Fund destinations (where money flows)

This helps identify:
- Who funded the address (victims)
- Where the address sends funds (suspects)

---

## 💰 Cash-Out Alerts

Automatically detects when funds are sent to known entities:
- Exchanges (Binance, Coinbase, Kraken)
- Bridges (Ronin, Poly Network)
- Mixing services (Tornado Cash)
- Other known services

Example alert:
```
⚠️ 50.5 ETH → Binance Hot Wallet
```

---

## 📈 Report Statistics

Your reports now show:
- **Total transactions**: Number of transactions analyzed
- **Total inflow**: Sum of all incoming ETH
- **Total outflow**: Sum of all outgoing ETH
- **Net flow**: Inflow - Outflow (positive = accumulating)
- **Unique senders**: How many different addresses sent funds
- **Unique receivers**: How many different addresses received funds
- **Average transaction**: Mean ETH per transaction
- **Median transaction**: Middle value of all transactions
- **Max transaction**: Largest single transaction

---

## 🤖 AI Analysis (Gemini)

Your tool now includes three AI-powered analyses:

### 1. Forensic Narrative
- Overall assessment of transaction behavior
- AML technique identification
- Professional tone and terminology
- Fallback if API unavailable

### 2. Pattern Analysis
- Explanation of each detected pattern
- AML concern level assessment
- Justification for findings
- Recommended investigation steps

### 3. Risk Assessment
- Profile of top destination addresses
- Exchange/service identification
- Red flag indicators
- Monitoring recommendations

---

## 📁 Output Files Generated

When you generate a report, these files are created in `/exports/`:

1. **forensic_report.pdf** - Main report (5-7 pages)
2. **transaction_chart.png** - Flow visualization
3. **address_distribution.png** - Top addresses chart
4. **graph.gexf** - Network graph (for Gephi)

---

## 🔐 Data Privacy

- No address → person identification
- Professional AML/CFT terminology
- Suitable for legal review
- No personally identifiable information
- Reports focus on transaction patterns and risk

---

## 🚨 Example Scenarios

### Scenario 1: Clean Address
```
- Few transactions
- Low velocity
- Consistent partners
- Risk: LOW (5-15/100)
→ Report: Normal activity, no concerns
```

### Scenario 2: Mixing Service (Suspicious)
```
- 200+ transactions
- Many different senders
- Consolidation pattern
- Risk: HIGH (65-75/100)
→ Report: Mixing service behavior, AML concern
```

### Scenario 3: Hack/Theft (Critical)
```
- Rapid succession (many in <1 min)
- Large inflow then quick outflow
- Direct exchange transfer
- Risk: CRITICAL (85-95/100)
→ Report: Urgent - likely theft with quick liquidation
```

---

## 🔧 Customization

To add more known entities, edit `analyzer.py`:

```python
KNOWN_ENTITIES = {
    "0xaddress": "Entity Name",
    "0xanother": "Service Name",
}
```

To adjust risk weights, edit `calculate_risk_score()` in `analyzer.py`

---

## 📞 Usage Tips

1. **Use specific date ranges** - Narrows down to periods of interest
2. **Check multiple addresses** - Track fund flow across network
3. **Compare reports** - Identify patterns across addresses
4. **Export network graph** - Visualize relationships in Gephi
5. **Review risk factors** - Understand what triggered high score

---

## ⚠️ Limitations

- Free tier Gemini API has rate limits (falls back to template analysis)
- Etherscan data limited to public blockchain
- Only analyzes ETH mainnet transactions
- Cannot identify individuals from addresses
- Requires valid Etherscan API key

---

## 🎓 Professional Terminology

Your reports use industry-standard AML/CFT terms:
- **Structuring**: Breaking large amounts into smaller transfers
- **Mixing**: Consolidating inputs from multiple sources
- **Layering**: Obfuscating transaction trails
- **Cash-out**: Converting to fiat/withdrawing funds
- **Consolidation**: Combining funds into single wallet
- **Velocity**: Transaction frequency and speed

---

**Your tool is now suitable for:**
✅ Compliance investigations
✅ Fraud detection
✅ Money laundering analysis
✅ Forensic audits
✅ Risk assessment
✅ Legal review and documentation

---

Version: 2.0 - Full Forensic Suite
Status: Production Ready ✅
