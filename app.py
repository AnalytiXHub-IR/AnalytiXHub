import os
from flask import Flask, render_template, request, send_file, flash, jsonify, redirect, url_for
from dotenv import load_dotenv
import networkx as nx
import json
from datetime import datetime, timedelta

# Custom Modules
from analyzer import analyze_csv, analyze_live_eth, analyze_multiple_addresses
from eth_live import fetch_eth_address, fetch_eth_address_with_counts
from report import create_pdf
from gemini import generate_comprehensive_analysis, generate_narrative
from case_manager import Case, CaseManager
from visualizations import create_timeline_visualization, create_sankey_diagram, create_heatmap_visualization
from legal_report import LegalReportGenerator
from batch_analyzer import BatchAnalyzer

# Multi-Chain & Advanced Features
try:
    from multi_chain import MultiChainFetcher
    MULTI_CHAIN_AVAILABLE = True
except:
    MULTI_CHAIN_AVAILABLE = False

try:
    from advanced_analysis import AddressClustering, ThreatIntelligence, AnomalyDetector
    ADVANCED_FEATURES_AVAILABLE = True
except:
    ADVANCED_FEATURES_AVAILABLE = False

# NEW FEATURES (v4.0) - Taint Analysis, Smart Contracts, DeFi, Real-time Monitor, Threat Intel
try:
    from taint_analysis import TaintAnalyzer
    TAINT_ANALYSIS_AVAILABLE = True
except ImportError:
    TAINT_ANALYSIS_AVAILABLE = False

try:
    from smart_contract_analyzer import SmartContractAnalyzer
    SMART_CONTRACT_AVAILABLE = True
except ImportError:
    SMART_CONTRACT_AVAILABLE = False

try:
    from defi_analyzer import DeFiAnalyzer
    DEFI_ANALYZER_AVAILABLE = True
except ImportError:
    DEFI_ANALYZER_AVAILABLE = False

try:
    from real_time_monitor import RealTimeMonitor
    REALTIME_MONITOR_AVAILABLE = True
except ImportError:
    REALTIME_MONITOR_AVAILABLE = False

try:
    from threat_intelligence import ThreatIntelligenceAPI, BlockchainIntelligence
    THREAT_INTEL_V2_AVAILABLE = True
except ImportError:
    THREAT_INTEL_V2_AVAILABLE = False

# Database Integration
try:
    from db_models import (
        SessionLocal, Base, engine, Case as DBCase, Address, Transaction, 
        SmartContract, DeFiActivity, TaintTrace, MonitoringJob, ThreatIntel, 
        AnomalyDetection, AddressCluster
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

load_dotenv()
app = Flask(__name__)
app.secret_key = "forensic_key_secret"

# Celery Configuration
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

from celery import Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")

# Initialize case manager
case_manager = CaseManager()

current_case = {
    "summary": None,
    "findings": [],
    "analysis": {},  # Comprehensive AI analysis
    "source": None,
    "chain": "ethereum",  # Default chain
    "address": None,
    "addresses": [],  # For batch processing
    "clustering_results": {},  # Cross-address clustering
    "threat_intel_results": {},  # Threat intelligence flags
    "anomalies": [],  # ML-detected anomalies
}

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET"])
def index():
    """Case Management Dashboard"""
    cases = case_manager.list_cases()
    # Sort cases by creation date (newest first)
    cases.sort(key=lambda x: x.created_at, reverse=True)
    return render_template("case_list.html", cases=cases)

@app.route("/case/<case_id>/dashboard", methods=["GET"])
def case_dashboard(case_id):
    """Specific Case Dashboard"""
    case = case_manager.get_case(case_id)
    if not case:
        flash("Case not found", "error")
        return redirect(url_for("index"))
    
    # Set as active case context (simple way for now)
    global current_case
    # In a real app, we'd load this from persistent storage or re-hydrate
    # keeping the simple global/current_case structure for now but scoped
    
    return render_template("case_dashboard.html", active_case=case)

@app.route("/case/<case_id>/investigation", methods=["GET", "POST"])
def investigation(case_id):
    """Investigation Tool for a specific Case"""
    case = case_manager.get_case(case_id)
    if not case:
        flash("Case not found", "error")
        return redirect(url_for("index"))
        
    global current_case
    from eth_live import SUPPORTED_CHAINS
    supported_chains = SUPPORTED_CHAINS
    
    # Note: POST logic is moved to /api/stream_analysis for real-time feedback
    # This route now primarily serves the view
    
    return render_template("investigation.html", 
                         active_case=case,
                         summary=current_case.get("summary"), 
                         tx_counts=current_case.get('counts'), 
                         source=current_case.get('source'), 
                         fetch_options=current_case.get('fetch_options', {}),
                         supported_chains=supported_chains,
                         current_chain=current_case.get('chain', 'ethereum'),
                         clustering_results=current_case.get('clustering_results', {}),
                         threat_intel=current_case.get('threat_intel_results', {}),
                         anomalies=current_case.get('anomalies', []),
                         taint_results=current_case.get('taint_results', {}))

@app.route("/api/case/<case_id>/analysis/stream", methods=["POST"])
def stream_analysis(case_id):
    """Stream analysis progress and results"""
    from flask import Response, stream_with_context
    from eth_live import SUPPORTED_CHAINS
    
    case = case_manager.get_case(case_id)
    if not case: return jsonify({"error": "Case not found"}), 404
    
    address = request.form.get("address")
    chain_name = request.form.get("chain", "ethereum")
    chain_id = SUPPORTED_CHAINS.get(chain_name.lower(), 1)
    # Parse logic args
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    include_internal = request.form.get('include_internal') == 'on'
    include_token_transfers = request.form.get('include_token_transfers') == 'on'
    
    # Store context
    current_case["chain"] = chain_name
    current_case["chain_id"] = chain_id
    current_case["address"] = address
    
    def generate():
        try:
            yield json.dumps({"type": "progress", "msg": f"Initiating trace for {address[:10]}...", "progress": 10}) + "\n"
            
            # 1. Add to case tracking
            case.add_address(address, tag="target", notes=f"Analysis started on {datetime.now()}")
            case_manager.save_case(case)
            yield json.dumps({"type": "progress", "msg": "Address added to case tracking.", "progress": 20}) + "\n"
            
            # 2. Fetch Data
            if ETHERSCAN_KEY:
                yield json.dumps({"type": "progress", "msg": f"Fetching transactions from {chain_name}...", "progress": 30}) + "\n"
                
                txs, counts = fetch_eth_address_with_counts(
                    address, ETHERSCAN_KEY,
                    chain_id=chain_id,
                    include_internal=include_internal,
                    include_token_transfers=include_token_transfers
                )
                
                yield json.dumps({"type": "info", "data": counts, "msg": f"Fetched {len(txs)} transactions."}) + "\n"
                yield json.dumps({"type": "progress", "msg": "Analyzing transaction patterns...", "progress": 50}) + "\n"
                
                # 3. Basic Analysis
                summary, G, source = analyze_live_eth(
                    txs, address, 
                    start_date=start_date, end_date=end_date, chain_id=chain_id
                )
                
                current_case["summary"] = summary
                current_case["source"] = source
                current_case["counts"] = counts
                current_case["fetch_options"] = {"include_internal": include_internal, "include_token_transfers": include_token_transfers}
                
                yield json.dumps({"type": "progress", "msg": "Running advanced forensics...", "progress": 70}) + "\n"
                
                # 4. Advanced Features
                if ADVANCED_FEATURES_AVAILABLE and txs:
                    try:
                        yield json.dumps({"type": "progress", "msg": "Clustering related addresses...", "progress": 75}) + "\n"
                        current_case["clustering_results"] = AddressClustering.cluster_addresses(txs, address)
                    except: pass
                    
                    try:
                        yield json.dumps({"type": "progress", "msg": "Detecting anomalies...", "progress": 80}) + "\n"
                        current_case["anomalies"] = AnomalyDetector.detect_anomalies(txs)
                    except: pass
                    
                    try:
                        yield json.dumps({"type": "progress", "msg": "Checking threat intelligence databases...", "progress": 85}) + "\n"
                        threat_data = ThreatIntelligence.load_threat_data()
                        current_case["threat_intel_results"] = ThreatIntelligence.check_address(address, threat_data)
                    except: pass
                
                if TAINT_ANALYSIS_AVAILABLE and txs:
                    try:
                         yield json.dumps({"type": "progress", "msg": "Tracing fund flow paths...", "progress": 90}) + "\n"
                         taint = TaintAnalyzer()
                         current_case["taint_results"] = taint.trace_fund_flow(address, txs)
                    except: pass
                
                yield json.dumps({"type": "progress", "msg": "Analysis complete. Rendering results...", "progress": 100}) + "\n"
                yield json.dumps({"type": "complete", "redirect": url_for('investigation', case_id=case_id)}) + "\n"
            else:
                 yield json.dumps({"type": "error", "msg": "API Key missing."}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "msg": str(e)}) + "\n"
            
    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

@app.route("/report", methods=["POST"])
def report():
    if not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
        
    print("[+] Generating comprehensive forensic report...")
    print(f"[+] Querying Gemini AI for detailed analysis...")
    
    # Generate comprehensive AI analysis
    analysis_results = generate_comprehensive_analysis(
        current_case["summary"], 
        current_case["findings"]
    )
    current_case["analysis"] = analysis_results
    
    # Extract narrative from results dict (fallback already handled in gemini.py)
    narrative = analysis_results.get("narrative") if isinstance(analysis_results, dict) else analysis_results
    if not narrative or "[Analysis failed" in str(narrative):
        narrative = generate_narrative(
            current_case["summary"], 
            current_case["findings"]
        )
    
    # Create comprehensive PDF report
    create_pdf(current_case["summary"], current_case["findings"], narrative, current_case["source"])
    
    return send_file("exports/forensic_report.pdf", as_attachment=True, 
                    download_name=f"Forensic_Report_{current_case['address'][:10]}.pdf")

# GEXF Download Route
@app.route("/downloads/graph.gexf", methods=["GET"])
def download_gexf():
    """Download network graph in GEXF format for Gephi"""
    gexf_path = "exports/graph.gexf"
    
    if os.path.exists(gexf_path):
        return send_file(gexf_path, as_attachment=True, 
                        download_name=f"Transaction_Network_{current_case.get('address', 'network')[:10]}.gexf")
    
    return "Graph file not found. Please run an analysis first.", 404

# Timeline Visualization Route
@app.route("/timeline", methods=["POST"])
def timeline():
    """Generate interactive timeline visualization"""
    if not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
    
    address = current_case.get("address")
    chain_id = current_case.get("chain_id", 1)
    txs_data = fetch_eth_address(address, ETHERSCAN_KEY, chain_id=chain_id, include_internal=True, include_token_transfers=True) if ETHERSCAN_KEY else []
    
    timeline_file = create_timeline_visualization(txs_data, address)
    
    if timeline_file and os.path.exists(timeline_file):
        return send_file(timeline_file, as_attachment=True, download_name="timeline.html")
    
    return "Failed to generate timeline", 500

# Sankey Diagram Route
@app.route("/sankey", methods=["POST"])
def sankey():
    """Generate Sankey fund flow diagram"""
    if not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
    
    address = current_case.get("address")
    sankey_file = create_sankey_diagram(current_case["summary"], address)
    
    if sankey_file and os.path.exists(sankey_file):
        return send_file(sankey_file, as_attachment=True, download_name="sankey.html")
    
    return "Failed to generate Sankey diagram", 500

# Legal/FIR Report Route
@app.route("/legal_report", methods=["POST"])
def legal_report():
    """Generate FIR-ready legal report"""
    if not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
    
    investigator = request.form.get("investigator", "Unknown Officer")
    department = request.form.get("department", "Cybercrime Division")
    case_id = request.form.get("case_id", "2024001")
    
    # Generate AI analysis
    analysis_results = generate_comprehensive_analysis(
        current_case["summary"], 
        current_case["findings"]
    )
    
    # Create legal report
    legal_gen = LegalReportGenerator(case_id, investigator, department)
    report_file = legal_gen.create_fir_report(
        current_case["summary"],
        analysis_results,
        current_case.get("address")
    )
    
    if report_file and os.path.exists(report_file):
        return send_file(report_file, as_attachment=True, 
                        download_name=f"FIR_Report_{case_id}.pdf")
    
    return "Failed to generate legal report", 500

# Multi-Address Analysis Route
@app.route("/analyze_multiple", methods=["POST"])
def analyze_multiple():
    """Analyze multiple addresses from CSV"""
    if 'csv_file' not in request.files:
        return "No CSV file provided", 400
    
    csv_file = request.files['csv_file']
    if csv_file.filename == '':
        return "No file selected", 400
    
    # Save temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        csv_file.save(tmp.name)
        temp_path = tmp.name
    
    try:
        # Run batch analysis
        batch = BatchAnalyzer()
        results = batch.analyze_from_csv(temp_path)
        
        # Generate reports
        csv_report = batch.generate_csv_report()
        json_report = batch.generate_json_report()
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return jsonify({
            'success': True,
            'total_analyzed': len(results),
            'results': results,
            'csv_file': csv_report,
            'json_file': json_report,
            'summary': batch.export_summary()
        })
        
    except Exception as e:
        os.unlink(temp_path)
        return jsonify({'success': False, 'error': str(e)}), 500

# Case Management Routes
@app.route("/case/create", methods=["POST"])
def create_case():
    """Create new case"""
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
    """Add address to case"""
    address = request.form.get("address")
    tag = request.form.get("tag", "unknown")  # victim, suspect, intermediary, exchange
    
    if case_manager.add_address_to_case(case_id, address, tag):
        return jsonify({'success': True, 'message': f"Address {address[:10]}... added to case"})
    
    return jsonify({'success': False, 'error': 'Case not found'}), 404

@app.route("/case/<case_id>/add_note", methods=["POST"])
def add_note_to_case(case_id):
    """Add note to case"""
    note = request.form.get("note", "")
    
    if case_manager.add_note_to_case(case_id, note):
        return jsonify({'success': True, 'message': "Note added"})
    
    return jsonify({'success': False, 'error': 'Case not found'}), 404

@app.route("/case/<case_id>/report", methods=["GET"])
def case_report(case_id):
    """Generate case report"""
    case = case_manager.get_case(case_id)
    
    if not case:
        return "Case not found", 404
    
    # Generate comprehensive case report
    report_content = f"""
CASE INVESTIGATION REPORT
========================
Case ID: {case.case_id}
Case Name: {case.name}
Investigator: {case.investigator}
Created: {case.created_at}

DESCRIPTION:
{case.description}

ADDRESSES TRACKED:
"""
    
    for addr, data in case.addresses.items():
        report_content += f"\n- {addr}\n  Tag: {data['tag']}\n  Notes: {data['notes']}"
    
    report_content += f"\n\nINVESTIGATION NOTES:\n"
    for note in case.notes:
        report_content += f"- {note}\n"
    
    return report_content, 200, {'Content-Type': 'text/plain'}

# Heatmap Visualization Route
@app.route("/heatmap", methods=["POST"])
def heatmap():
    """Generate activity heatmap"""
    if not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
    
    address = current_case.get("address")
    chain_id = current_case.get("chain_id", 1)
    txs_data = fetch_eth_address(address, ETHERSCAN_KEY, chain_id=chain_id, include_internal=True, include_token_transfers=True) if ETHERSCAN_KEY else []
    
    heatmap_file = create_heatmap_visualization(txs_data, address)
    
    if heatmap_file and os.path.exists(heatmap_file):
        return send_file(heatmap_file, as_attachment=True, download_name="activity_heatmap.png")
    
    return "Failed to generate heatmap", 500


# ==================== BATCH PROCESSING ROUTE (#8) ====================

@app.route("/batch", methods=["GET", "POST"])
def batch_processing():
    """Batch analyze multiple addresses"""
    from eth_live import SUPPORTED_CHAINS
    results = {}
    batch_status = None
    
    if request.method == "POST":
        addresses_input = request.form.get("addresses", "")
        chain_name = request.form.get("chain", "ethereum")
        chain_id = SUPPORTED_CHAINS.get(chain_name.lower(), 1)
        
        if addresses_input:
            addresses = [addr.strip() for addr in addresses_input.split('\n') if addr.strip()]
            current_case["addresses"] = addresses
            
            try:
                print(f"[+] Batch processing {len(addresses)} addresses on {chain_name}...")
                batch_status = {
                    "total": len(addresses),
                    "processed": 0,
                    "results": []
                }
                
                for i, address in enumerate(addresses):
                    try:
                        # Fetch transactions using V2 API
                        txs, counts = fetch_eth_address_with_counts(
                            address, 
                            ETHERSCAN_KEY,
                            chain_id=chain_id
                        )
                        
                        # Analyze
                        summary, G, source = analyze_live_eth(
                            txs, 
                            address,
                            chain_id=chain_id,
                            chain_name=chain_name
                        )
                        
                        # Threat check
                        threat = {}
                        if ADVANCED_FEATURES_AVAILABLE:
                            threat_data = ThreatIntelligence.load_threat_data()
                            threat = ThreatIntelligence.check_address(address, threat_data)
                        
                        batch_status["results"].append({
                            "address": address,
                            "transactions": counts.get('normal', 0),
                            "risk_score": summary.get('risk_score', 0),
                            "is_flagged": threat.get('is_flagged', False),
                            "threats": threat.get('threat_sources', [])
                        })
                        
                        batch_status["processed"] += 1
                        print(f"  [{i+1}/{len(addresses)}] {address} - Risk: {summary.get('risk_score', 0)}")
                    
                    except Exception as e:
                        print(f"  [ERROR] {address}: {e}")
                        batch_status["results"].append({
                            "address": address,
                            "error": str(e)
                        })
                
                results = batch_status["results"]
                flash(f"✓ Batch analysis complete: {batch_status['processed']}/{batch_status['total']} addresses processed", "success")
            
            except Exception as e:
                flash(f"Batch processing error: {str(e)}", "error")

# ==================== CASE SPECIFIC ROUTES ====================


@app.route("/case/<case_id>/board")
def case_board(case_id):
    """Investigation Board View"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    return render_template("board.html", active_case=case)

@app.route("/case/<case_id>/asset/add", methods=["POST"])
def add_board_asset(case_id):
    """Add item to investigation board"""
    asset_type = request.form.get("type")
    content = request.form.get("content")
    
    # Handle Image Uploads
    if asset_type == "image":
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                # Ensure uploads dir exists
                upload_dir = os.path.join("static", "uploads", case_id)
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file
                filename = f"{datetime.now().strftime('%H%M%S')}_{file.filename}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                # Content is relative path for frontend
                content = f"/static/uploads/{case_id}/{filename}"
    
    if case_manager.add_asset_to_case(case_id, asset_type, content):
        return redirect(url_for('case_board', case_id=case_id))
    
    return "Failed to add asset", 400

@app.route("/case/<case_id>/asset/delete/<asset_id>", methods=["POST"])
def delete_board_asset(case_id, asset_id):
    """Delete item from investigation board"""
    case_manager.delete_asset_from_case(case_id, asset_id)
    return redirect(url_for('case_board', case_id=case_id))

@app.route("/case/<case_id>/asset/move/<asset_id>", methods=["POST"])
def move_board_asset(case_id, asset_id):
    """Update asset position on board"""
    data = request.get_json()
    case = case_manager.get_case(case_id)
    if case:
        for asset in case.assets:
            if asset["id"] == asset_id:
                asset["position"] = {"x": data["x"], "y": data["y"]}
                break
        case_manager.save_case(case)
        return jsonify({"status": "success"})
    return jsonify({"error": "Case not found"}), 404

@app.route("/case/<case_id>/visualizations")
def case_visualizations(case_id):
    """Visualizations Dashboard for a Case"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    # Use current_case data for now if available
    return render_template("visualizations.html", 
                         active_case=case,
                         summary=current_case.get("summary"),
                         tx_counts=current_case.get("counts"))

@app.route("/case/<case_id>/charts")
def case_charts(case_id):
    """Redirect for legacy link"""
    return redirect(url_for("case_visualizations", case_id=case_id))

@app.route("/case/<case_id>/clustering")
def case_clustering(case_id):
    """Clustering View for a Case"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    return render_template("clustering.html", 
                         active_case=case,
                         clustering_results=current_case.get("clustering_results", {}))

@app.route("/case/<case_id>/threat-intel")
def case_threat_intel(case_id):
    """Threat Intel View for a Case"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    return render_template("threat_intel.html", 
                         active_case=case,
                         threat=current_case.get("threat_intel_results", {}),
                         anomalies=current_case.get("anomalies", []))

@app.route("/case/<case_id>/monitoring")
def case_monitoring(case_id):
    """Real-time Monitoring View"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    return render_template("monitoring.html", active_case=case)

@app.route("/case/<case_id>/reports")
def case_reports(case_id):
    """Reports Generation Hub"""
    case = case_manager.get_case(case_id)
    if not case: return redirect(url_for("index"))
    
    return render_template("reports.html", active_case=case, summary=current_case.get("summary"))

# =============================================================


# ==================== CLUSTERING DETAILS ROUTE (#2) ====================

@app.route("/clustering")
def clustering_details():
    """View cross-address clustering results"""
    clustering = current_case.get("clustering_results", {})
    return render_template("clustering.html", clustering=clustering)


# ==================== THREAT INTEL ROUTE (#7) ====================

@app.route("/threat-intel")
def threat_intel():
    """View threat intelligence results"""
    threat = current_case.get("threat_intel_results", {})
    anomalies = current_case.get("anomalies", [])
    return render_template("threat_intel.html", threat=threat, anomalies=anomalies)


# ==================== ANOMALY DETAILS ROUTE (#9) ====================

@app.route("/anomalies")
def anomalies():
    """View ML-detected anomalies"""
    anomaly_list = current_case.get("anomalies", [])
    return render_template("anomalies.html", anomalies=anomaly_list)


# ==================== SUPPORTED CHAINS ROUTE ====================

@app.route("/api/chains")
def api_chains():
    """Get supported chains - unified V2 endpoint"""
    from eth_live import SUPPORTED_CHAINS
    # Return all supported chains with V2 endpoint
    chains_data = {}
    for name, chain_id in SUPPORTED_CHAINS.items():
        chains_data[name] = {"chain_id": chain_id, "endpoint": "https://api.etherscan.io/v2/api"}
    return jsonify(chains_data)


# ==================== NEW ROUTES FOR v4.0 FEATURES ====================

@app.route("/taint-analysis")
def taint_analysis_view():
    """View taint analysis results"""
    taint = current_case.get("taint_results", {})
    return render_template("taint_analysis.html", taint=taint)


@app.route("/smart-contract-analysis")
def smart_contract_view():
    """View smart contract analysis results"""
    contract = current_case.get("contract_results", {})
    return render_template("smart_contract.html", contract=contract)


@app.route("/defi-activity")
def defi_activity_view():
    """View DeFi activity results"""
    defi = current_case.get("defi_results", {})
    return render_template("defi_activity.html", defi=defi)


@app.route("/api/address/<address>")
def api_address_details(address):
    """Get detailed address analysis via API"""
    if not DB_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        db = SessionLocal()
        # Get all analysis results for address
        addr_records = db.query(Address).filter_by(address=address).all()
        taint_records = db.query(TaintTrace).filter(
            (TaintTrace.source_address == address) | 
            (TaintTrace.destination_address == address)
        ).all()
        defi_records = db.query(DeFiActivity).filter_by(address=address).all()
        contract_records = db.query(SmartContract).filter_by(contract_address=address).all()
        
        return jsonify({
            "address": address,
            "analyses": len(addr_records),
            "taint_traces": len(taint_records),
            "defi_activities": len(defi_records),
            "smart_contracts": len(contract_records),
            "data": {
                "addresses": [r.to_dict() if hasattr(r, 'to_dict') else {} for r in addr_records],
                "taints": [{"source": r.source_address, "dest": r.destination_address, "type": r.taint_type} for r in taint_records],
                "defi": [{"protocol": r.protocol, "type": r.activity_type} for r in defi_records],
                "contracts": [{"address": r.contract_address, "risk": r.vulnerability_score} for r in contract_records]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/api/case/<case_id>/export")
def api_export_case(case_id):
    """Export case data with all analysis results"""
    if not DB_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        db = SessionLocal()
        case = db.query(DBCase).filter_by(case_id=case_id).first()
        
        if not case:
            return jsonify({"error": "Case not found"}), 404
        
        export_data = {
            "case": {
                "id": case.case_id,
                "name": case.case_name,
                "description": case.description,
                "investigator": case.investigator,
                "created_at": str(case.created_at),
                "status": case.status
            },
            "addresses": [a.to_dict() if hasattr(a, 'to_dict') else {} for a in case.addresses],
            "taint_traces": [
                {
                    "source": t.source_address,
                    "destination": t.destination_address,
                    "depth": t.trace_depth,
                    "type": t.taint_type,
                    "confidence": t.confidence
                } 
                for t in db.query(TaintTrace).filter_by(case_id=case.id).all()
            ],
            "smart_contracts": [
                {
                    "address": c.contract_address,
                    "risk_score": c.vulnerability_score,
                    "is_honeypot": c.is_honeypot,
                    "is_rug_pull": c.is_rug_pull
                }
                for c in db.query(SmartContract).filter_by(case_id=case.id).all()
            ],
            "defi_activities": [
                {
                    "address": d.address,
                    "protocol": d.protocol,
                    "type": d.activity_type,
                    "usd_value": d.usd_value
                }
                for d in db.query(DeFiActivity).filter_by(case_id=case.id).all()
            ],
            "anomalies": [
                {
                    "address": a.address,
                    "type": a.anomaly_type,
                    "score": a.anomaly_score
                }
                for a in db.query(AnomalyDetection).filter_by(case_id=case.id).all()
            ]
        }
        
        return jsonify(export_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000, use_reloader=False)
