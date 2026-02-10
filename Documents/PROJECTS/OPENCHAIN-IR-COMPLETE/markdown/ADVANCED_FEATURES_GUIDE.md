# OPENCHAIN IR - Advanced Features Quick Start Guide

## 🚀 Getting Started with New Features

### Prerequisites
- Python 3.10+
- All dependencies from `requirements.txt` installed
- Etherscan API key configured in `.env`
- Flask server running on localhost:5000

---

## 📊 Feature 1: Timeline Visualization

### What It Does
Creates an interactive timeline showing all transactions for an address over time.

### How to Use
1. Analyze an address first (using main analysis page)
2. Click "Generate Timeline" button
3. Download interactive timeline.html
4. Open in any web browser for interactive exploration

### Output Format
- Interactive Plotly chart (HTML)
- X-axis: Transaction timestamp
- Y-axis: Transaction amount (ETH)
- Green dots: Inbound transactions
- Red diamonds: Outbound transactions
- Hover for transaction details

### Use Case
Perfect for law enforcement to show judges/prosecutors chronological transaction patterns and identify suspicious timing patterns.

---

## 💰 Feature 2: Sankey Diagram (Fund Flow)

### What It Does
Visualizes the flow of funds from sources through the target address to destinations.

### How to Use
1. Analyze an address first
2. Click "Generate Sankey" button
3. Download sankey.html
4. Open in browser to see interactive fund flow visualization

### Output Format
- Interactive Sankey diagram
- Source addresses (green) → Target address (blue) → Destination addresses (red)
- Width of flows = ETH amount
- Shows top 5 sources and destinations

### Use Case
Excellent for demonstrating money laundering patterns and fund routing to law enforcement audiences.

---

## ⚖️ Feature 3: Legal Report (FIR Format)

### What It Does
Generates a court-admissible First Information Report (FIR) ready for law enforcement filing.

### How to Use
```
POST /legal_report
Parameters:
  - investigator: "Your Name"
  - department: "Cybercrime Division"
  - case_id: "2024001"
```

### Report Sections
1. **Case Information**
   - FIR number, date, investigating officer
   
2. **Key Findings Table**
   - Risk score, confidence level, transaction counts
   
3. **Forensic Analysis**
   - AI-generated narrative of findings
   
4. **Risk Assessment**
   - Categorized as LOW/MEDIUM/HIGH RISK
   
5. **Chain of Custody**
   - Evidence tracking documentation
   
6. **Blockchain Verification**
   - Details of data source and verification method
   
7. **Investigator Certification**
   - Signature line and certification

### Output Format
- Professional PDF document
- Multi-page format
- Admissible in court proceedings
- Includes blockchain verification details

### Use Case
File directly with police FIR system as digital evidence documentation.

---

## 🔍 Feature 4: Entity Recognition

### What It Does
Automatically identifies and classifies Ethereum addresses (exchanges, mixers, DEXs, etc.)

### How to Use
- **Automatic**: Runs with every analysis
- Returns entity type in analysis results
- Displays in reports

### Entity Types Recognized
- **Exchange**: Centralized crypto exchanges (Binance, Kraken, etc.)
- **Mixer**: Mixing services/tumblers
- **DEX**: Decentralized exchanges (Uniswap, SushiSwap, etc.)
- **Bridge**: Cross-chain bridge protocols
- **DeFi**: DeFi protocols (Aave, Compound, etc.)
- **Individual**: User-controlled wallets

### Output
- Entity type automatically assigned
- Risk level per entity
- Included in all analysis results

### Use Case
Quickly identify what type of entity an address belongs to without manual research.

---

## 📐 Feature 5: Sankey Diagram Advanced

### What It Does
Creates publication-quality fund flow visualizations suitable for presentations.

### Customization Options
- Adjustable time windows
- Filtering by amount threshold
- Color schemes for different risk levels

### Output Formats
- **Interactive HTML** - For web exploration
- **Static PNG** - For reports and presentations

### Use Case
Perfect for presentation slides showing fund flows to law enforcement audiences.

---

## 📋 Feature 6: Batch Analysis

### What It Does
Analyze multiple cryptocurrency addresses simultaneously and generate comparison reports.

### How to Use

**Step 1: Prepare CSV File**
```csv
address,tag,notes
0x1234...5678,suspect,Known mixer address
0xabcd...efgh,victim,Fraud victim wallet
0x5678...9012,intermediary,Intermediary address
```

**Step 2: Upload and Analyze**
```
POST /analyze_multiple
File: addresses.csv
```

**Step 3: Get Results**
- Summary statistics
- Risk score comparison
- Pattern detection across all addresses
- Entity type classification

### Output Reports
1. **CSV Report** - Easy import to Excel
2. **JSON Report** - For programmatic use
3. **Text Report** - Human-readable summary
4. **Statistics** - Aggregated metrics

### Statistics Included
- Average risk score across batch
- Max/min risk scores
- Average confidence levels
- Total ETH received/sent
- Pattern frequency analysis

### Use Case
Screen multiple suspect addresses in minutes, prioritize high-risk entities for detailed investigation.

---

## 📁 Feature 7: Case Management

### What It Does
Organize cryptocurrency investigations into cases with address tracking and notes.

### Basic Workflow

**Create a Case**
```
POST /case/create
Parameters:
  - case_name: "Operation Takedown - April 2024"
  - description: "Investigation into $2M fraud network"
  - investigator: "Detective Smith"
```

**Add Addresses to Case**
```
POST /case/{case_id}/add_address
Parameters:
  - address: "0x1234567890..."
  - tag: "victim" | "suspect" | "intermediary" | "exchange"
```

**Add Investigation Notes**
```
POST /case/{case_id}/add_note
Parameters:
  - note: "Cross-reference with bank transaction on 2024-01-15"
```

**Generate Case Report**
```
GET /case/{case_id}/report
```

### Data Persistence
- Cases saved as JSON files in `./cases/` directory
- Automatically loaded on startup
- No database required

### Use Case
Centralized case tracking for complex multi-address investigations.

---

## 📊 Feature 8: Confidence Scoring

### What It Does
Provides a confidence percentage (0-100%) for each analysis based on data completeness.

### How It Works
Calculates confidence based on:
- **Data Completeness**: Percentage of transactions with complete data
- **Sample Size**: Number of transactions analyzed
- **Pattern Clarity**: How distinct the patterns are
- **Time Coverage**: Period of data available

### Interpretation
- **90-100%**: Highly reliable analysis, significant data
- **70-89%**: Good confidence, sufficient patterns
- **50-69%**: Moderate confidence, some patterns clear
- **<50%**: Low confidence, limited data

### Usage in Reports
- Displayed prominently in legal reports
- Helps judges/prosecutors understand reliability
- Indicates need for further investigation

### Use Case
Legally defensible analysis - shows reliability level to court proceedings.

---

## 🎯 Complete Investigation Workflow

### Scenario: Investigating $500K Fraud Network

1. **Initial Analysis**
   - Analyze primary suspect wallet
   - Review risk score and patterns
   - Note confidence level

2. **Temporal Analysis**
   - Generate timeline visualization
   - Identify suspicious timing patterns
   - Note high-activity periods

3. **Fund Flow Analysis**
   - Generate Sankey diagram
   - Identify sources and destinations
   - Document layering patterns

4. **Case Organization**
   - Create case in case management
   - Add primary address as suspect
   - Document initial findings as notes

5. **Related Address Analysis**
   - Identify 10-15 related addresses from Sankey
   - Create batch CSV of addresses
   - Run batch analysis
   - Prioritize by risk score

6. **Detailed Investigation**
   - Analyze high-risk addresses individually
   - Add to case as victims/intermediaries
   - Add notes on relationships
   - Generate individual Sankey diagrams

7. **Legal Documentation**
   - Generate FIR legal report
   - Include timeline evidence
   - Document chain of custody
   - Get investigator certification

8. **Case Report**
   - Generate comprehensive case report
   - Export as PDF
   - Share with prosecution
   - File with court

---

## 💡 Pro Tips

### Timeline Analysis
- Use for showing chronological evidence
- Timestamps prove deliberate patterns
- Good for demonstrating velocity

### Sankey Diagrams
- Best for visual presentations
- Shows complexity of network
- Demonstrates fund routing

### Batch Analysis
- Start with 20-30 addresses
- Sort by risk score
- Focus on top 5 high-risk addresses
- Use tags to categorize relationships

### Case Management
- Create separate case per investigation
- Use tags consistently (victim/suspect/etc.)
- Add notes documenting key findings
- Export case report regularly

### Legal Reports
- File within 30 days of analysis
- Include confidence scores
- Document all sources
- Get investigator certification

---

## 🔐 Data Security

- **Local Analysis**: All data processed locally, not sent to cloud
- **API Data**: Only Etherscan queries use internet (public blockchain data)
- **AI Analysis**: Optional Gemini AI uses rate-limited free tier
- **Report Export**: PDF files stored locally in exports/ directory
- **Case Data**: JSON files stored locally in cases/ directory

---

## ⚠️ Important Notes

1. **API Rate Limits**: Etherscan has rate limits on free tier - space out large batch analyses
2. **Data Accuracy**: Blockchain data is immutable but analysis is timestamp-dependent
3. **Confidence Scores**: Reflect data completeness, not pattern certainty
4. **Legal Review**: All FIR reports should be reviewed by legal counsel before filing
5. **Presentation**: Always include methodology when presenting findings

---

## 🆘 Troubleshooting

### Timeline Won't Generate
- Check if address has transaction history
- Verify Etherscan API key is valid
- Try smaller date range

### Sankey Diagram Empty
- Need at least 5+ transactions to destination
- Check if address is receiving/sending funds
- Review Sankey for single-transaction addresses

### Batch Analysis Slow
- Reduce batch size (try 5-10 addresses)
- Run during off-peak hours
- Check API rate limit status

### Legal Report Missing Data
- Ensure full analysis complete first
- Provide investigator name and department
- Verify case ID format

### Case Not Saving
- Check cases/ directory exists
- Verify write permissions to directory
- Try creating case with simpler name

---

## 📞 Support

For issues or questions:
1. Check analysis results for error messages
2. Review confidence scores - low scores may indicate data issues
3. Test with known addresses (Binance, major exchanges)
4. Verify Etherscan API key configuration

---

**Last Updated:** 2024
**Version:** 2.1
**Status:** ✅ Production Ready
