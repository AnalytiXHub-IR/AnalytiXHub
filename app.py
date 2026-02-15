import os
from flask import Flask, render_template, request, send_file, flash, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import networkx as nx
import json
from datetime import datetime, timedelta

# Custom Modules
from modules.analyzers.analyzer import analyze_csv, analyze_live_eth, analyze_multiple_addresses
import re
from modules.fetchers.eth_live import fetch_eth_address, fetch_eth_address_with_counts, fetch_transaction_details
from modules.reports.report import create_pdf
from modules.ai.gemini import generate_comprehensive_analysis, generate_narrative
from modules.core.case_manager import Case, CaseManager
from modules.utils.visualizations import create_timeline_visualization, create_sankey_diagram, create_heatmap_visualization
from modules.reports.legal_report import LegalReportGenerator
from modules.analyzers.batch_analyzer import BatchAnalyzer

# Breadcrumbs removed as requested
# from modules.fetchers.breadcrumbs_client import BreadcrumbsClient 
from modules.utils.pathfinder import PathFinder
from modules.utils.monitoring import MonitoringSystem
from modules.analyzers.ml_engine import ml_engine

monitoring_system = MonitoringSystem()
case_manager = CaseManager()

try:
    from modules.analyzers.advanced_analysis import AddressClustering, ThreatIntelligence, AnomalyDetector
    ADVANCED_FEATURES_AVAILABLE = True
except:
    ADVANCED_FEATURES_AVAILABLE = False

# NEW FEATURES (v4.0) - Taint Analysis, Smart Contracts, DeFi, Real-time Monitor, Threat Intel
try:
    from modules.analyzers.taint_analysis import TaintAnalyzer
    TAINT_ANALYSIS_AVAILABLE = True
except ImportError:
    TAINT_ANALYSIS_AVAILABLE = False

try:
    from modules.analyzers.smart_contract_analyzer import SmartContractAnalyzer
    SMART_CONTRACT_AVAILABLE = True
except ImportError:
    SMART_CONTRACT_AVAILABLE = False

try:
    from modules.analyzers.defi_analyzer import DeFiAnalyzer
    DEFI_ANALYZER_AVAILABLE = True
except ImportError:
    DEFI_ANALYZER_AVAILABLE = False

try:
    from modules.analyzers.real_time_monitor import RealTimeMonitor
    REALTIME_MONITOR_AVAILABLE = True
except ImportError:
    REALTIME_MONITOR_AVAILABLE = False

try:
    from modules.analyzers.threat_intelligence import ThreatIntelligenceAPI, BlockchainIntelligence
    THREAT_INTEL_V2_AVAILABLE = True
except ImportError:
    THREAT_INTEL_V2_AVAILABLE = False

# Database Integration
try:
    from modules.core.db_models import (
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

@app.route("/", methods=["GET"])
def index():
    """Dashboard - New Home Page"""
    active_cases = len(case_manager.list_cases())
    
    # Mock data for dashboard
    recent_activity = [
        {"title": "High Risk Alert", "description": "Address 0x123... flagged as mixing service", "timestamp": "2 mins ago", "user": "System"},
        {"title": "Case Created", "description": "Operation Red Dragon initialized", "timestamp": "1 hour ago", "user": "Investigator"},
        {"title": "Analysis Complete", "description": "Batch analysis of 50 addresses finished", "timestamp": "5 hours ago", "user": "System"},
    ]
    
    return render_template("dashboard.html", 
                         active_page="dashboard",
                         active_cases_count=active_cases,
                         high_alerts_count=3,
                         recent_activity=recent_activity)

import re
from modules.fetchers.eth_live import fetch_eth_address, fetch_eth_address_with_counts, fetch_transaction_details

# ... (existing imports)

@app.route("/investigation", methods=["GET", "POST"])
def investigation():
    """Investigation Tool - Formerly Index"""
    global current_case
    summary = None
    # Import chain IDs from eth_live module
    from modules.fetchers.eth_live import SUPPORTED_CHAINS
    supported_chains = SUPPORTED_CHAINS
    
    if request.method == "POST":
        address = request.form.get("address", "").strip()
        chain_name = request.form.get("chain", "ethereum")
        chain_id = SUPPORTED_CHAINS.get(chain_name.lower(), 1)  # Default to Ethereum
        
        # ===== ADVANCED SEARCH DISPATCHER =====
        address = address.strip() # Ensure no whitespace
        
        # 1. Transaction Hash (66 chars, 0x prefix)
        # Using a more robust regex
        if re.match(r'^0x[a-fA-F0-9]{64}$', address):
            print(f"[Search] Detected Transaction Hash: {address}")
            tx_details = fetch_transaction_details(address, ETHERSCAN_KEY, chain_id)
            if tx_details:
                return render_template("transaction.html", tx=tx_details, chain_name=chain_name)
            else:
                flash("Transaction not found or API error. Please check the hash and chain.", "error")
                return redirect(url_for('investigation'))

        # 2. Block Number (Integer)
        elif re.match(r'^\d+$', address):
            print(f"[Search] Detected Block Number: {address}")
            # Redirect to Etherscan for now as we don't have a block view
            return redirect(f"https://etherscan.io/block/{address}")
            
        # 3. Domain Name (.eth, .crypto, etc.)
        elif re.match(r'.+\.(eth|crypto|nft|wallet)$', address.lower(), re.IGNORECASE):
            print(f"[Search] Detected Domain: {address}")
            flash(f"Domain resolution for '{address}' is not yet configured. Please use the computed address.", "warning")
            # For now, just let it fall through to analysis? 
            # Or redirect to investigation to clear the POST?
            # Let's return investigation template with the warning
            return render_template("investigation.html", 
                                 supported_chains=supported_chains,
                                 current_case=current_case,
                                 summary={}, # Pass empty dict instead of None to avoid Jinja errors
                                 recent_activity=[],
                                 chain_name=chain_name)
            
        # 4. Standard Address (42 chars, 0x prefix) or fallback
        # Continue to standard analysis...
        
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        include_internal = True if request.form.get('include_internal') == 'on' else False
        include_token_transfers = True if request.form.get('include_token_transfers') == 'on' else False
        
        current_case["chain"] = chain_name
        current_case["chain_id"] = chain_id
        current_case["address"] = address
        
        # Determine Currency Symbol
        currency_map = {
            'ethereum': 'ETH', 'eth': 'ETH', 'sepolia': 'ETH', 'base': 'ETH', 'linea': 'ETH',
            'bitcoin': 'BTC', 'btc': 'BTC',
            'solana': 'SOL', 'sol': 'SOL',
            'tron': 'TRX', 'trx': 'TRX',
            'xrp': 'XRP', 'ripple': 'XRP',
            'bsc': 'BNB', 'binance': 'BNB',
            'polygon': 'MATIC', 'matic': 'MATIC',
            'optimism': 'OP', 'op': 'OP',
            'arbitrum': 'ARB', 'arb': 'ARB',
            'avalanche': 'AVAX',
            'fantom': 'FTM',
            'cronos': 'CRO',
            'moonbeam': 'GLMR',
            'gnosis': 'GNO',
            'celo': 'CELO',
            'blast': 'BLAST'
        }
        current_case["currency"] = currency_map.get(chain_name.lower(), 'UNIT')
        
        # Determine Explorer URL Pattern
        explorer_map = {
            'ethereum': 'https://etherscan.io/tx/',
            'bitcoin': 'https://mempool.space/tx/',
            'solana': 'https://solscan.io/tx/',
            'tron': 'https://tronscan.org/#/transaction/',
            'bsc': 'https://bscscan.com/tx/',
            'polygon': 'https://polygonscan.com/tx/',
            'optimism': 'https://optimistic.etherscan.io/tx/',
            'arbitrum': 'https://arbiscan.io/tx/',
            'avalanche': 'https://snowtrace.io/tx/',
            'fantom': 'https://ftmscan.com/tx/',
            'sepolia': 'https://sepolia.etherscan.io/tx/'
        }
        current_case["explorer_tx"] = explorer_map.get(chain_name.lower(), 'https://etherscan.io/tx/')
        
        if address:
            try:
                print(f"[+] Trace initiated: {address} on {chain_name} (Chain ID: {chain_id}) | {start_date} to {end_date}")
                
                # Unified Multi-Chain API Call (Supports EVM, Solana, Bitcoin, Tron)
                from modules.fetchers.multi_chain import MultiChainFetcher
                txs, counts = MultiChainFetcher.fetch_by_chain(
                    chain_name, 
                    address,
                    include_internal=include_internal,
                    include_token_transfers=include_token_transfers
                )
                
                # Comprehensive analysis
                summary, G, source = analyze_live_eth(
                    txs, address, 
                    start_date=start_date,
                    end_date=end_date,
                    chain_id=chain_id,
                    chain_name=chain_name
                )
                
                current_case["summary"] = summary
                current_case["transactions"] = txs  # <--- CRITICAL FIX
                current_case["source"] = source
                current_case["counts"] = counts
                current_case["fetch_options"] = {
                    "include_internal": include_internal,
                    "include_token_transfers": include_token_transfers
                }
                
                # ===== ADVANCED FEATURES =====
                
                # 1. Cross-Address Clustering (#2)
                if ADVANCED_FEATURES_AVAILABLE and txs:
                    try:
                        clustering = AddressClustering.cluster_addresses(txs, address, chain_id)
                        current_case["clustering_results"] = clustering
                        print(f"[+] Cross-address clustering: {len(clustering)} patterns detected")
                    except Exception as e:
                        print(f"[!] Clustering error: {e}")
                
                # 2. Threat Intelligence (#7)
                if ADVANCED_FEATURES_AVAILABLE:
                    try:
                        threat_data = ThreatIntelligence.load_threat_data()
                        threat_check = ThreatIntelligence.check_address(address, threat_data)
                        current_case["threat_intel_results"] = threat_check
                        if threat_check['is_flagged']:
                            print(f"[!] THREAT ALERT: Address flagged by {threat_check['threat_sources']}")
                    except Exception as e:
                        print(f"[!] Threat Intel error: {e}")
                else:
                    # Fallback Threat Intelligence (Mock/Basic)
                    is_bad = address.lower() in ['0x123', '0xbad'] # Placeholder
                    current_case["threat_intel_results"] = {
                        "is_flagged": is_bad,
                        "severity": "High" if is_bad else "Low",
                        "confidence": 0.0,
                        "threat_sources": [],
                        "threat_types": []
                    }
                
                # 3. ML Anomaly Detection (#9)
                if txs:
                    try:
                        # Use new ML Engine
                        anomalies = ml_engine.detect_anomalies(txs)
                        current_case["anomalies"] = anomalies
                        
                        # Use Pattern Recognition
                        patterns = ml_engine.detect_patterns(txs, address)
                        current_case["patterns"] = patterns
                        
                        print(f"[+] ML Engine: {len(anomalies)} anomalies, {len(patterns)} patterns detected")
                    except Exception as e:
                        print(f"[!] Anomaly detection error: {e}")
                
                # 4. TAINT ANALYSIS (#4) - NEW

                if TAINT_ANALYSIS_AVAILABLE and txs:
                    try:
                        taint = TaintAnalyzer(txs)
                        taint_results = taint.trace_fund_flow(address)
                        current_case["taint_results"] = taint_results
                        print(f"[+] Taint Analysis: Fund flow traced through {len(taint_results.get('path', []))} addresses")
                    except Exception as e:
                        print(f"[!] Taint analysis error: {e}")
                
                # 5. SMART CONTRACT ANALYSIS (#5) - NEW
                # Check if address is a contract
                if SMART_CONTRACT_AVAILABLE and address:
                    try:
                        contract_analyzer = SmartContractAnalyzer(ETHERSCAN_KEY)
                        contract_results = contract_analyzer.analyze_contract(address)
                        current_case["contract_results"] = contract_results
                        if contract_results:
                            print(f"[+] Smart Contract Analysis: Risk Score {contract_results.get('risk_score', 0)}/100")
                    except Exception as e:
                        print(f"[!] Contract analysis error: {e}")
                
                # 6. DEFI ACTIVITY TRACKING (#6) - NEW
                if DEFI_ANALYZER_AVAILABLE and address:
                    try:
                        defi = DeFiAnalyzer()
                        defi_results = {
                            "uniswap": defi.get_uniswap_swaps(address),
                            "uniswap_lp": defi.get_uniswap_positions(address),
                            "aave": defi.get_aave_user_data(address),
                            "curve": defi.get_curve_pool_activity(address)
                        }
                        current_case["defi_results"] = defi_results
                        total_activities = sum(len(v or []) for v in defi_results.values())
                        print(f"[+] DeFi Activity: {total_activities} total activities found")
                    except Exception as e:
                        print(f"[!] DeFi analysis error: {e}")
                
                # Database integration - Save results if DB available
                # TEMPORARILY DISABLED - Models need schema updates
                #if DB_AVAILABLE:
                if False:
                    try:
                        db = SessionLocal()
                        # Create case record
                        case_record = DBCase(
                            case_id=f"auto_{datetime.utcnow().timestamp()}",
                            case_name=f"Analysis: {address[:10]}...",
                            description=f"Automated analysis of {address}",
                            investigator="System",
                            status="completed"
                        )
                        db.add(case_record)
                        
                        # Save address
                        addr_record = Address(
                            case_id=case_record.id,
                            address=address,
                            chain=chain_name,
                            risk_score=summary.get('risk_score', 0),
                            tag="analyzed"
                        )
                        db.add(addr_record)
                        
                        # Save taint trace if available
                        if "taint_results" in current_case:
                            taint_data = current_case["taint_results"]
                            taint_record = TaintTrace(
                                case_id=case_record.id,
                                source_address=address,
                                destination_address=taint_data.get("final_destination", address),
                                trace_depth=taint_data.get("depth", 0),
                                taint_type=taint_data.get("type", "unknown"),
                                confidence=taint_data.get("confidence", 0.0)
                            )
                            db.add(taint_record)
                        
                        # Save smart contract analysis if available
                        if "contract_results" in current_case:
                            contract = current_case["contract_results"]
                            contract_record = SmartContract(
                                case_id=case_record.id,
                                contract_address=address,
                                vulnerability_score=contract.get("risk_score", 0),
                                is_honeypot=contract.get("is_honeypot", False),
                                is_rug_pull=contract.get("is_rug_pull", False)
                            )
                            db.add(contract_record)
                        
                        # Save anomalies
                        if current_case.get("anomalies"):
                            for anomaly in current_case["anomalies"]:
                                anom_record = AnomalyDetection(
                                    case_id=case_record.id,
                                    address=address,
                                    anomaly_type=anomaly.get("type", "unknown"),
                                    anomaly_score=anomaly.get("score", 0)
                                )
                                db.add(anom_record)
                        
                        db.commit()
                        print(f"[+] Database: Analysis results saved to PostgreSQL")
                    except Exception as e:
                        print(f"[!] Database save error: {e}")
                        try:
                            db.rollback()
                        except:
                            pass
                
                # Network graph
                os.makedirs("exports", exist_ok=True)
                nx.write_gexf(G, "exports/graph.gexf")
                
                current_case["findings"] = [
                    f"Target: {address}",
                    f"Chain: {chain_name.upper()}",
                    f"Period: {start_date if start_date else 'All Time'} to {end_date if end_date else 'Present'}",
                    f"Transactions: {summary.get('total_transactions', 0)}",
                    f"Net Flow: {summary['net_flow']}",
                    f"Risk Score: {summary.get('risk_score', 0)}/100",
                    f"Clusters Found: {len(current_case.get('clustering_results', {}))}",
                    f"Threat Flagged: {'YES' if current_case['threat_intel_results'].get('is_flagged') else 'NO'}",
                    f"Anomalies: {len(current_case.get('anomalies', []))}",
                    f"Smart Contract Risk: {current_case.get('contract_results', {}).get('risk_score', 'N/A')}/100" if "contract_results" in current_case else None,
                    f"DeFi Activities: {sum(len(v or []) for v in current_case.get('defi_results', {}).values())}" if "defi_results" in current_case else None,
                ]
                current_case["findings"] = [f for f in current_case["findings"] if f is not None]
                
                flash(f"✓ Analysis complete: {summary['total_transactions']} transactions analyzed on {chain_name}", "success")

            except Exception as e:
                print(f"[ERROR] {e}")
                flash(f"Error: {str(e)}", "error")

                # print(f"[DEBUG] Validation - Transactions in current_case: {len(current_case.get('transactions', []))}")
                # print(f"[DEBUG] Validation - Summary Total: {summary.get('total_transactions')}")
                # if len(current_case.get('transactions', [])) > 0:
                #    print(f"[DEBUG] Sample Transaction: {current_case['transactions'][0]}")

    return render_template("investigation.html", 
                         active_page="investigation",
                         summary=summary, 
                         tx_counts=current_case.get('counts'), 
                         source=current_case.get('source'), 
                         fetch_options=current_case.get('fetch_options', {}),
                         supported_chains=supported_chains,
                         current_chain=current_case.get('chain', 'ethereum'),
                         current_address=current_case.get('address'),
                         clustering_results=current_case.get('clustering_results', {}),
                         threat_intel=current_case.get('threat_intel_results', {}),
                         anomalies=current_case.get('anomalies', []),
                         patterns=current_case.get('patterns', []),
                         recent_activity=current_case.get('transactions', []),
                         taint_results=current_case.get('taint_results', {}),
                         contract_results=current_case.get('contract_results', {}),
                         defi_results=current_case.get('defi_results', {}),
                         currency=current_case.get('currency', 'UNIT'),
                         explorer_tx=current_case.get('explorer_tx', 'https://etherscan.io/tx/'))

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
    
    # USE EXISTING TRANSACTIONS (Multi-Chain Support)
    txs_data = current_case.get("transactions", [])
    if not txs_data and ETHERSCAN_KEY:
         # Fallback only if no data
         txs_data = fetch_eth_address(address, ETHERSCAN_KEY, chain_id=chain_id, include_internal=True, include_token_transfers=True)
    
    timeline_file = create_timeline_visualization(txs_data, address)
    
    if timeline_file and os.path.exists(timeline_file):
        return send_file(timeline_file, as_attachment=True, download_name="timeline.html")
    
    flash("Failed to generate timeline. Ensure analysis data is available.", "error")
    return redirect(url_for('investigation'))

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
    
    flash("Failed to generate Sankey diagram. Ensure enough transaction data exists.", "error")
    return redirect(url_for('investigation'))

@app.route("/heatmap", methods=["POST"])
def heatmap():
    """Generate Heatmap"""
    if not current_case["summary"]:
        return "No data available.", 400
        
    address = current_case.get("address")
    txs_data = current_case.get("transactions", [])
    
    heatmap_file = create_heatmap_visualization(txs_data, address)
    
    if heatmap_file and os.path.exists(heatmap_file):
        return send_file(heatmap_file, as_attachment=True, download_name="heatmap.png")
        
    return "Failed to generate heatmap", 500

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
@app.route("/cases", methods=["GET"])
def list_cases():
    """List all cases"""
    cases = case_manager.list_cases()
    # Sort by created_at desc
    cases.sort(key=lambda x: x.created_at, reverse=True)
    
    current_context = None
    if 'active_case_id' in session:
         active_case = case_manager.get_case(session['active_case_id'])
         if active_case:
             current_context = {'id': active_case.case_id, 'name': active_case.name}

    return render_template("cases.html", 
                         active_page="cases",
                         cases=cases,
                         current_case_context=current_context)

@app.route("/cases/create", methods=["POST"])
def create_case_route():
    """Create new case (Form submission)"""
    case_name = request.form.get("case_name", "Untitled Case")
    description = request.form.get("description", "")
    investigator = request.form.get("investigator", "Unknown")
    
    case = case_manager.create_case(case_name, description, investigator)
    
    # Auto-switch to new case
    session['active_case_id'] = case.case_id
    flash(f"Case '{case_name}' created and set as active.", "success")
    
    return redirect(url_for('list_cases')) # Or redirect to case detail

@app.route("/cases/delete/<case_id>", methods=["POST"])
def delete_case_route(case_id):
    """Delete a case"""
    if case_manager.delete_case(case_id):
        if session.get('active_case_id') == case_id:
            session.pop('active_case_id', None)
        return jsonify({'success': True, 'message': 'Case deleted'})
    return jsonify({'success': False, 'error': 'Failed to delete case'}), 400

@app.route("/cases/switch/<case_id>")
def switch_case(case_id):
    """Set active case context"""
    case = case_manager.get_case(case_id)
    if case:
        session['active_case_id'] = case_id
        flash(f"Switched to case: {case.name}", "success")
    else:
        flash("Case not found", "error")
    return redirect(request.referrer or url_for('list_cases'))

@app.route("/cases/close")
def close_active_case():
    """Close current active case context"""
    session.pop('active_case_id', None)
    flash("Active case closed.", "info")
    return redirect(request.referrer or url_for('list_cases'))

@app.route("/cases/<case_id>")
def case_detail(case_id):
    """View case details"""
    case = case_manager.get_case(case_id)
    if not case:
        flash("Case not found", "error")
        return redirect(url_for('list_cases'))
        
    return render_template("case_detail.html", case=case, active_page="cases")

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




# ==================== BATCH PROCESSING ROUTE (#8) ====================

# ==================== SEED DATA ROUTES ====================
@app.route("/cases/seed/wannacry")
def seed_wannacry():
    case = case_manager.seed_wannacry_case()
    flash(f"Seeded case: {case.name}", "success")
    return redirect(url_for('case_details', case_id=case.case_id))

# ==================== BATCH PROCESSING ROUTE (#8) ====================

@app.route("/batch", methods=["GET", "POST"])
def batch_processing():
    """Batch analyze multiple addresses"""
    from modules.fetchers.eth_live import SUPPORTED_CHAINS
    results = {}
    batch_status = None
    
    if request.method == "POST":
        # Handle CSV Upload
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file.filename != '':
                import pandas as pd
                try:
                    df = pd.read_csv(file)
                    # Normalize columns
                    df.columns = [c.lower().strip() for c in df.columns]
                    
                    # Check if it's a Transaction List (Graph Generation)
                    if 'from' in df.columns and 'to' in df.columns:
                        print(f"[Batch] Detected Transaction CSV with {len(df)} rows")
                        G = nx.DiGraph()
                        
                        for _, row in df.iterrows():
                            # Determine if EVM (for lowercasing) or other (preserve case)
                            # Simple heuristic: if 'chain' column exists, use it. Otherwise default to Ethereum (lowercase)
                            chain_col = row.get('chain', 'ethereum').lower()
                            is_evm = chain_col in ['ethereum', 'eth', 'bsc', 'matic', 'polygon', 'arbitrum', 'optimism']
                            
                            src = str(row['from']).strip()
                            dst = str(row['to']).strip()
                            
                            if is_evm:
                                src = src.lower()
                                dst = dst.lower()
                            
                            val = row.get('value', row.get('amount', 0))
                            
                            # Add nodes
                            G.add_node(src, label=src[:8])
                            G.add_node(dst, label=dst[:8])
                            
                            # Add edge
                            G.add_edge(src, dst, weight=float(val) if val else 0)
                            
                        # Export GEXF
                        os.makedirs("exports", exist_ok=True)
                        nx.write_gexf(G, "exports/graph.gexf")
                        
                        batch_status = {
                            "processed": len(df),
                            "graph_file": True,
                            "results": [] # No deep analysis for graph import
                        }
                        flash(f"✓ Graph generated from {len(df)} transactions. Download enabled.", "success")
                        
                    # Else treat as Address List
                    elif 'address' in df.columns or 'addr' in df.columns:
                        addresses = df['address'].dropna().unique().tolist() if 'address' in df.columns else df['addr'].dropna().unique().tolist()
                        print(f"[Batch] Detected Address CSV with {len(addresses)} addresses")
                        
                    else:
                        flash("Invalid CSV format. Need 'From/To' columns for Graph or 'Address' for Analysis.", "error")
                        
                except Exception as e:
                    flash(f"Error processing CSV: {str(e)}", "error")

        # Handle Manual Input (or fallthrough from CSV Address extraction)
        addresses_input = request.form.get("addresses", "")
        chain_name = request.form.get("chain", "ethereum")
        chain_id = SUPPORTED_CHAINS.get(chain_name.lower(), 1)

        if addresses_input:
            addresses = [addr.strip() for addr in addresses_input.split('\n') if addr.strip()]
        
        # If we extracted addresses from CSV, they are in 'addresses' local var
        # Check if 'addresses' variable exists and is not empty
        if 'addresses' in locals() and addresses:
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
    
    return render_template("batch.html", results=results, batch_status=batch_status)


# ==================== CLUSTERING DETAILS ROUTE (#2) ====================

# ==================== TRACING ROUTE ====================
@app.route("/tracing")
def tracing():
    """Visual Tracing Interface"""
    current_address = current_case.get("address")
    return render_template("tracing.html", active_page="tracing", current_address=current_address)

@app.route("/api/trace/<address>")
def api_trace(address):
    """Get graph data for Cytoscape"""
    from modules.fetchers.breadcrumbs_client import BreadcrumbsClient
    from modules.utils.pathfinder import PathFinder
    
    # Get chain_id from query (default to 1 'Ethereum')
    chain_arg = request.args.get('chain', '1')
    
    # Check for Dogecoin
    if str(chain_arg).lower() in ['dogecoin', 'doge']:
        try:
            from modules.fetchers.multi_chain import MultiChainFetcher
            txs, _ = MultiChainFetcher.fetch_by_chain('dogecoin', address)
            
            # Convert to Cytoscape Elements
            elements = []
            # Add Root
            elements.append({
                'data': {'id': address, 'label': address[:8], 'full_address': address, 'type': 'root', 'risk': 0, 'icon': '/static/images/doge_icon.png'}
            })
            
            for tx in txs:
                sender = tx.get('from')
                receiver = tx.get('to')
                val = tx.get('value', 0)
                
                # Add Nodes
                if sender and sender != address:
                     elements.append({'data': {'id': sender, 'label': sender[:8], 'full_address': sender, 'type': 'wallet', 'risk': 0}})
                if receiver and receiver != address:
                     elements.append({'data': {'id': receiver, 'label': receiver[:8], 'full_address': receiver, 'type': 'wallet', 'risk': 0}})
                     
                # Add Edge
                edge_id = f"{sender}_{receiver}_{tx.get('hash')}"
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': sender,
                        'target': receiver,
                        'label': f"{val:.2f} DOGE",
                        'amount': val,
                        'hash': tx.get('hash')
                    }
                })
            
            return jsonify(elements)
        except Exception as e:
             return jsonify({"error": str(e)}), 500

    chain_id = chain_arg
    auto_mode = request.args.get('auto', 'false').lower() == 'true'
    
    client = BreadcrumbsClient(ETHERSCAN_KEY)
    
    try:
        if auto_mode:
            print(f"[DEBUG] Auto-Scan triggered for {address}")
            elements = client.scan_all_chains(address)
        else:
            elements = client.get_graph_data(address, chain_id=chain_id)
            
        return jsonify(elements)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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


# ==================== SETTINGS ROUTE ====================
@app.route("/settings", methods=["GET"])
def settings():
    """System configuration page"""
    # Pass current config to template (safely)
    config_data = {
        'ETHERSCAN_API_KEY': os.getenv('ETHERSCAN_API_KEY'),
        'SOLANA_API_KEY': os.getenv('SOLANA_API_KEY'),
        'TRON_API_KEY': os.getenv('TRON_API_KEY'),
        'ABUSEIPDB_API_KEY': os.getenv('ABUSEIPDB_API_KEY'),
        'DB_AVAILABLE': DB_AVAILABLE,
        'THREAT_INTEL_V2_AVAILABLE': THREAT_INTEL_V2_AVAILABLE
    }
    return render_template("settings.html", active_page="settings", config=config_data)

@app.route("/settings/update", methods=["POST"])
def update_settings():
    """Update system settings (API keys)"""
    # In a real app, we'd update .env or a db
    # For now, just flash a message as we can't easily hot-reload .env in this env
    flash("Settings saved. Note: For persistent API key updates, please edit the .env file directly in this development environment.", "info")
    return redirect(url_for('settings'))

# ==================== SUPPORTED CHAINS ROUTE ====================

@app.route("/api/pathfinder")
def api_pathfinder():
    """Find path between two addresses"""
    import os
    source = request.args.get('source')
    target = request.args.get('target')
    chain_id = request.args.get('chain', 1)
    
    if not source or not target:
        return jsonify({"error": "Missing source or target address"}), 400
        
    from modules.utils.pathfinder import PathFinder
    pf = PathFinder()
    try:
        result = pf.find_path(source, target, chain_id)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== MONITORING ROUTES ====================
@app.route("/monitoring")
def monitoring_ui():
    watchlist = monitoring_system.get_watchlist()
    alerts = monitoring_system.get_alerts()
    return render_template("monitoring.html", watchlist=watchlist, alerts=alerts, active_page="monitoring")

@app.route("/api/monitoring/add", methods=["POST"])
def add_monitor():
    address = request.form.get("address")
    chain = request.form.get("chain", "ethereum")
    tag = request.form.get("tag", "watchlist")
    
    if monitoring_system.add_address(address, chain, tag):
        flash(f"Address {address} added to watchlist.", "success")
    else:
        flash(f"Address {address} is already being monitored.", "warning")
        
    return redirect(url_for('monitoring_ui'))

@app.route("/api/monitoring/remove/<path:address>")
def remove_monitor(address):
    if monitoring_system.remove_address(address):
        flash(f"Address {address} removed from watchlist.", "success")
    else:
        flash("Address not found in watchlist.", "error")
    return redirect(url_for('monitoring_ui'))

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


# ==================== INVESTIGATOR ROUTE (Phase 3) ====================

@app.route("/investigator", methods=["GET"])
def investigator():
    """New Graph Investigator Tab"""
    return render_template("investigator.html", active_page="investigator")

@app.route("/api/graph_data", methods=["GET"])
def api_graph_data():
    """API to fetch graph data for the Investigator tab"""
    address = request.args.get("address")
    chain = request.args.get("chain", "ethereum")
    
    if not address:
        return jsonify({"error": "No address provided"}), 400
        
    try:
        # Use Breadcrumbs Client
        from modules.fetchers.breadcrumbs_client import BreadcrumbsClient
        BREADCRUMBS_KEY = "81CGNLRY9ICK6HOK5D52XIG6D7RXG5"
        client = BreadcrumbsClient(etherscan_key=ETHERSCAN_KEY, breadcrumbs_key=BREADCRUMBS_KEY)
        
        # Determine chain_id for MultiChain fallback if needed in Client
        # Determine chain_id for MultiChain fallback if needed in Client
        from modules.fetchers.eth_live import SUPPORTED_CHAINS
        chain_id = SUPPORTED_CHAINS.get(chain.lower(), 1)
        if chain.lower() == 'bitcoin': chain_id = 0 # Dummy ID for non-EVM
        if chain.lower() == 'solana': chain_id = -1
        if chain.lower() == 'tron': chain_id = -2
        
        # DOGECOIN HANDLER
        if chain.lower() in ['dogecoin', 'doge']:
             print(f"[Investigator] Fetching Dogecoin graph for {address}...")
             from modules.fetchers.multi_chain import MultiChainFetcher
             txs, _ = MultiChainFetcher.fetch_by_chain('dogecoin', address)
             
             # Convert to Cytoscape (Investigator format)
             elements = []
             # Root
             elements.append({'data': {'id': address, 'label': address[:6], 'full_address': address, 'type': 'root', 'chain': 'dogecoin', 'risk': 0}, 'classes': 'root'})
             
             for tx in txs:
                 sender = tx.get('from', 'Unknown')
                 receiver = tx.get('to', 'Unknown')
                 val = tx.get('value', 0)
                 
                 # Add Nodes
                 if sender != address:
                     elements.append({'data': {'id': sender, 'label': sender[:6], 'full_address': sender, 'type': 'wallet', 'chain': 'dogecoin', 'risk': 10}})
                 if receiver != address:
                     elements.append({'data': {'id': receiver, 'label': receiver[:6], 'full_address': receiver, 'type': 'wallet', 'chain': 'dogecoin', 'risk': 10}})
                     
                 # Add Edge
                 elements.append({
                     'data': {
                         'id': f"{sender}_{receiver}_{tx.get('hash', '')[:5]}", 
                         'source': sender, 
                         'target': receiver,
                         'label': f"{val:.1f} DOGE",
                         'value': val
                     }
                 })
             return jsonify({"elements": elements})
        
        print(f"[Investigator] Fetching graph for {address} on {chain}...")
        elements = client.get_graph_data(address, chain_id=chain_id)
        
        return jsonify({"elements": elements})
        
    except Exception as e:
        print(f"[!] Graph API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
