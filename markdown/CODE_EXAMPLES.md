# OPENCHAIN IR v2.1 - Feature Code Examples

## 8 Advanced Features with Code Examples

---

## Feature 1: Multi-Address Tracking

### Code Example
```python
from analyzer import analyze_multiple_addresses
from eth_live import fetch_eth_address

# Track funds across network of addresses
addresses = [
    "0x1234...5678",
    "0xabcd...efgh", 
    "0x5678...9012"
]

results = analyze_multiple_addresses(
    addresses, 
    api_key=ETHERSCAN_KEY,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Returns: {
#   'networks': [...addresses...],
#   'links': [...relationships...],
#   'risk_summary': {...},
#   'graph': NetworkX graph object
# }
```

### Flask Route
```python
@app.route("/analyze_multiple", methods=["POST"])
def analyze_multiple():
    csv_file = request.files['csv_file']
    batch = BatchAnalyzer()
    results = batch.analyze_from_csv(csv_file.name)
    return jsonify({
        'success': True,
        'results': results,
        'csv_file': batch.generate_csv_report(),
        'json_file': batch.generate_json_report()
    })
```

---

## Feature 2: Timeline Visualization

### Code Example
```python
from visualizations import create_timeline_visualization
import os

# Create interactive timeline
txlist = fetch_eth_address("0x1234...5678", api_key)
timeline_file = create_timeline_visualization(
    txlist, 
    "0x1234...5678",
    output_file="exports/timeline.html"
)

# Returns: "exports/timeline.html"
# Output: Interactive Plotly chart with:
#   - X-axis: Transaction timestamps
#   - Y-axis: ETH amounts
#   - Green markers: Inbound transactions
#   - Red diamonds: Outbound transactions
#   - Hover details with transaction info
```

### Flask Route
```python
@app.route("/timeline", methods=["POST"])
def timeline():
    if not current_case["summary"]:
        return "No data available", 400
    
    address = current_case.get("address")
    txs_data = fetch_eth_address(address, ETHERSCAN_KEY)
    timeline_file = create_timeline_visualization(txs_data, address)
    
    return send_file(timeline_file, as_attachment=True, 
                    download_name="timeline.html")
```

---

## Feature 3: Legal Report (FIR Format)

### Code Example
```python
from legal_report import LegalReportGenerator

# Create FIR-ready legal report
legal_gen = LegalReportGenerator(
    case_id="CYBER/2024001",
    investigator_name="Detective Smith",
    department="Cybercrime Division"
)

report_file = legal_gen.create_fir_report(
    summary=analysis_summary,
    analysis=ai_analysis,
    root_address="0x1234...5678",
    output_file="exports/FIR_Report_2024001.pdf"
)

# Returns: "exports/FIR_Report_2024001.pdf"
# Contains:
#   - Case information section
#   - Key findings table
#   - Forensic analysis
#   - Risk assessment (LOW/MEDIUM/HIGH)
#   - Chain of custody documentation
#   - Blockchain verification details
#   - Investigator certification
```

### Flask Route
```python
@app.route("/legal_report", methods=["POST"])
def legal_report():
    investigator = request.form.get("investigator", "Unknown Officer")
    department = request.form.get("department", "Cybercrime Division")
    case_id = request.form.get("case_id", "2024001")
    
    analysis_results = generate_comprehensive_analysis(
        current_case["summary"], 
        current_case["findings"]
    )
    
    legal_gen = LegalReportGenerator(case_id, investigator, department)
    report_file = legal_gen.create_fir_report(
        current_case["summary"],
        analysis_results,
        current_case.get("address")
    )
    
    return send_file(report_file, as_attachment=True, 
                    download_name=f"FIR_Report_{case_id}.pdf")
```

---

## Feature 4: Entity Recognition

### Code Example
```python
from analyzer import identify_entity_type, KNOWN_ENTITIES

# Auto-identify entity type
address = "0x3f5CE5FBFE3E9af3971dD833d26bA9b5C85F9Cf"

entity_type = identify_entity_type(address)
# Returns: "Exchange"

# Known entities database
if address in KNOWN_ENTITIES:
    entity_data = KNOWN_ENTITIES[address]
    print(f"Entity: {entity_data['name']}")
    print(f"Type: {entity_data['type']}")
    print(f"Risk: {entity_data['risk_level']}")

# Integration in analysis
summary = analyze_live_eth(txlist, address)
print(f"Entity Type: {summary['entity_type']}")  # Returns: "Exchange"
print(f"Risk Score: {summary['risk_score']}")    # Returns: 15
```

### Entity Types
```python
ENTITY_TYPES = {
    'exchange': 'Centralized cryptocurrency exchange',
    'mixer': 'Mixing service or tumbler',
    'dex': 'Decentralized exchange',
    'bridge': 'Cross-chain bridge protocol',
    'defi': 'DeFi protocol or smart contract',
    'individual': 'User-controlled wallet',
    'unknown': 'Unable to determine entity type'
}
```

---

## Feature 5: Sankey Diagrams

### Code Example
```python
from visualizations import create_sankey_diagram

# Create fund flow visualization
summary = analyze_live_eth(txlist, address)
sankey_file = create_sankey_diagram(
    summary,
    address,
    output_file="exports/sankey.html"
)

# Returns: "exports/sankey.html"
# Visualizes:
#   - Source addresses (green) → Root address (blue) → Destinations (red)
#   - Flow width represents ETH amount
#   - Top 5 sources and destinations
#   - Interactive hover with transaction details
```

### Flask Route
```python
@app.route("/sankey", methods=["POST"])
def sankey():
    if not current_case["summary"]:
        return "No data available", 400
    
    address = current_case.get("address")
    sankey_file = create_sankey_diagram(current_case["summary"], address)
    
    if sankey_file and os.path.exists(sankey_file):
        return send_file(sankey_file, as_attachment=True, 
                        download_name="sankey.html")
    
    return "Failed to generate Sankey diagram", 500
```

---

## Feature 6: Batch Analysis

### Code Example
```python
from batch_analyzer import BatchAnalyzer
import csv

# Prepare CSV file
# addresses.csv:
# address,tag,notes
# 0x1234...5678,suspect,Known mixer
# 0xabcd...efgh,victim,Fraud victim
# 0x5678...9012,intermediary,Intermediary

# Run batch analysis
batch = BatchAnalyzer(output_dir="exports/batch_analysis")
results = batch.analyze_from_csv("addresses.csv")

# Generate reports
csv_report = batch.generate_csv_report()      # CSV file
json_report = batch.generate_json_report()    # JSON file
txt_report = batch.generate_comparison_report()  # Text file

# Get summary statistics
stats = batch.get_summary_statistics()
# Returns: {
#   'total_addresses': 3,
#   'avg_risk_score': 45.5,
#   'max_risk_score': 78,
#   'min_risk_score': 12,
#   'unique_patterns': set(['consolidation', 'round_amounts']),
#   'total_eth_received': 125.5,
#   'total_eth_sent': 98.3
# }
```

### Flask Route
```python
@app.route("/analyze_multiple", methods=["POST"])
def analyze_multiple():
    if 'csv_file' not in request.files:
        return "No CSV file provided", 400
    
    csv_file = request.files['csv_file']
    batch = BatchAnalyzer()
    results = batch.analyze_from_csv(csv_file.name)
    
    return jsonify({
        'success': True,
        'total_analyzed': len(results),
        'results': results,
        'csv_file': batch.generate_csv_report(),
        'json_file': batch.generate_json_report(),
        'summary': batch.export_summary()
    })
```

---

## Feature 7: Case Management

### Code Example
```python
from case_manager import CaseManager, Case

# Initialize case manager
case_manager = CaseManager()

# Create new case
case = case_manager.create_case(
    name="Operation Takedown - Q1 2024",
    description="Investigation into $2M fraud network",
    investigator="Detective Smith"
)
case_id = case.case_id  # Auto-generated UUID

# Add addresses to case
case_manager.add_address_to_case(
    case_id,
    address="0x1234...5678",
    tag="suspect",  # Options: victim, suspect, intermediary, exchange
    notes="Primary suspect wallet"
)

case_manager.add_address_to_case(
    case_id,
    address="0xabcd...efgh",
    tag="victim",
    notes="Fraud victim wallet - stolen funds traced here"
)

# Add investigation notes
case_manager.add_note_to_case(
    case_id,
    content="Cross-referenced with bank transaction from 2024-01-15. Match confirmed.",
    address="0x1234...5678"
)

# Retrieve case
case = case_manager.get_case(case_id)
print(f"Case: {case.name}")
print(f"Addresses: {len(case.addresses)}")
print(f"Notes: {len(case.notes)}")

# Save and reload (automatic on app restart)
case_manager.save_all_cases()
```

### Flask Routes
```python
@app.route("/case/create", methods=["POST"])
def create_case():
    case_name = request.form.get("case_name", "Untitled Case")
    description = request.form.get("description", "")
    investigator = request.form.get("investigator", "Unknown")
    
    case = case_manager.create_case(case_name, description, investigator)
    
    return jsonify({
        'success': True,
        'case_id': case.case_id,
        'message': f"Case '{case_name}' created successfully"
    })

@app.route("/case/<case_id>/add_address", methods=["POST"])
def add_address_to_case(case_id):
    address = request.form.get("address")
    tag = request.form.get("tag", "unknown")
    
    if case_manager.add_address_to_case(case_id, address, tag):
        return jsonify({'success': True, 'message': f"Address added"})
    
    return jsonify({'success': False, 'error': 'Case not found'}), 404

@app.route("/case/<case_id>/add_note", methods=["POST"])
def add_note_to_case(case_id):
    note = request.form.get("note", "")
    
    if case_manager.add_note_to_case(case_id, note):
        return jsonify({'success': True, 'message': "Note added"})
    
    return jsonify({'success': False, 'error': 'Case not found'}), 404

@app.route("/case/<case_id>/report", methods=["GET"])
def case_report(case_id):
    case = case_manager.get_case(case_id)
    
    if not case:
        return "Case not found", 404
    
    report_content = f"""
CASE INVESTIGATION REPORT
========================
Case ID: {case.case_id}
Case Name: {case.name}
Investigator: {case.investigator}

ADDRESSES:
"""
    for addr, data in case.addresses.items():
        report_content += f"- {addr}: {data['tag']}\n"
    
    return report_content, 200, {'Content-Type': 'text/plain'}
```

---

## Feature 8: Confidence Scoring

### Code Example
```python
from analyzer import calculate_confidence_score, analyze_live_eth

# Calculate confidence in analysis
txlist = fetch_eth_address(address, api_key)
summary = analyze_live_eth(txlist, address)

# Get confidence score (automatically included in summary)
confidence = summary['confidence_score']
# Returns: 75 (percent)

# Interpretation
if confidence >= 90:
    reliability = "Highly Reliable"
elif confidence >= 70:
    reliability = "Good Confidence"
elif confidence >= 50:
    reliability = "Moderate Confidence"
else:
    reliability = "Low Confidence"

print(f"Analysis Confidence: {confidence}% ({reliability})")

# Factors affecting confidence
# - Data completeness (% of transactions with full details)
# - Sample size (number of transactions)
# - Pattern clarity (distinct patterns detected)
# - Time coverage (period of data available)
```

### Integration in Reports
```python
# In legal report
confidence = summary.get('confidence_score', 0)
report_text = f"""
Based on the analysis of {summary['total_transactions']} transactions 
with {confidence}% confidence level, this assessment is considered 
{'HIGHLY RELIABLE' if confidence > 85 else 'RELIABLE' if confidence > 70 else 'MODERATELY RELIABLE'}.
"""

# In risk assessment
risk_score = summary.get('risk_score', 0)
confidence = summary.get('confidence_score', 0)

assessment = f"""
Risk Score: {risk_score}/100
Confidence: {confidence}%
Reliability: {'High' if confidence > 85 else 'Moderate' if confidence > 60 else 'Low'}
"""
```

---

## Complete Integration Example

### Full Investigation Workflow
```python
# 1. Analyze primary address
summary = analyze_live_eth(txlist, "0x1234...5678")

# 2. Create case
case = case_manager.create_case(
    name="Fraud Investigation 2024",
    description="$500K cryptocurrency fraud",
    investigator="Detective Smith"
)

# 3. Add primary address
case_manager.add_address_to_case(
    case.case_id,
    "0x1234...5678",
    tag="suspect"
)

# 4. Generate timeline
create_timeline_visualization(txlist, "0x1234...5678")

# 5. Generate Sankey
create_sankey_diagram(summary, "0x1234...5678")

# 6. Identify related addresses
for victim_addr, amount in summary['top_victims']:
    case_manager.add_address_to_case(
        case.case_id,
        victim_addr,
        tag="victim"
    )

# 7. Batch analyze related addresses
batch = BatchAnalyzer()
related_addresses = [addr for addr, _ in summary['top_victims']]
batch_results = batch.analyze_from_list(related_addresses)

# 8. Generate FIR report
legal_gen = LegalReportGenerator(
    case_id=case.case_id,
    investigator_name="Detective Smith",
    department="Cybercrime Division"
)
legal_gen.create_fir_report(summary, ai_analysis, "0x1234...5678")

# 9. Generate case report
case_report = case_manager.get_case(case.case_id)

# 10. Export all results
print(f"✅ Investigation complete")
print(f"Case ID: {case.case_id}")
print(f"Addresses tracked: {len(case.addresses)}")
print(f"Confidence: {summary['confidence_score']}%")
print(f"Risk Level: {summary['risk_score']}/100")
```

---

## Flask Routes Summary

```python
# Visualization Routes
POST /timeline           # Generate timeline
POST /sankey            # Generate Sankey diagram
POST /heatmap           # Generate activity heatmap

# Legal Routes
POST /legal_report      # Generate FIR report

# Batch Analysis
POST /analyze_multiple  # Batch CSV analysis

# Case Management
POST /case/create       # Create case
POST /case/<id>/add_address  # Add address
POST /case/<id>/add_note     # Add note
GET  /case/<id>/report       # Generate report
```

---

## Output Files Generated

| Feature | File | Format | Location |
|---------|------|--------|----------|
| Timeline | timeline.html | HTML | exports/ |
| Sankey | sankey.html | HTML | exports/ |
| Legal Report | FIR_Report_XXXX.pdf | PDF | exports/ |
| Batch CSV | batch_analysis_results.csv | CSV | exports/batch_analysis/ |
| Batch JSON | batch_analysis_results.json | JSON | exports/batch_analysis/ |
| Batch TXT | batch_analysis.txt | TXT | exports/batch_analysis/ |
| Heatmap | activity_heatmap.png | PNG | exports/ |
| Cases | {case_id}.json | JSON | cases/ |

---

**All 8 features fully implemented and ready for deployment!** ✅
