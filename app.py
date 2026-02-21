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
# from modules.core.case_manager import Case, CaseManager # Deprecated
from modules.utils.visualizations import create_timeline_visualization, create_sankey_diagram, create_heatmap_visualization
from modules.reports.legal_report import LegalReportGenerator
from modules.analyzers.batch_analyzer import BatchAnalyzer

# Breadcrumbs removed as requested
# from modules.fetchers.breadcrumbs_client import BreadcrumbsClient 
from modules.utils.pathfinder import PathFinder
from modules.utils.monitoring import MonitoringSystem
from modules.analyzers.ml_engine import ml_engine

monitoring_system = MonitoringSystem()
# case_manager = CaseManager() # Deprecated

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
        AnomalyDetection, AddressCluster, init_db, Alert, CaseNote
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "forensic_key_secret_default_unsafe")

# Initialize Authentication
from flask_login import current_user, login_required
from modules.core.auth import auth_bp, init_auth, AuthUser

init_auth(app)
app.register_blueprint(auth_bp)

ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")

# Database Initialization
if __name__ == '__main__':
    with app.app_context():
        init_db()
        # Create default admin user if not exists
        from modules.core.db_models import User, SessionLocal
        from werkzeug.security import generate_password_hash
        
        db = SessionLocal()
        if not db.query(User).first():
            print("[INFO] Creating default admin user (admin/admin)")
            admin = User(
                username="admin", 
                email="admin@openchain.ir",
                password_hash=generate_password_hash("admin"),
                role="admin"
            )
            db.add(admin)
            db.commit()
        db.close()

# Helper to get active case from DB
def get_active_case():
    """Fetch active case from session ID"""
    case_id = session.get('active_case_id')
    if not case_id:
        return None
    
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.id == case_id).first()
    db.close()
    return case

@app.route("/", methods=["GET"])
@login_required # Protect Dashboard
def dashboard():
    """Case Management Dashboard"""
    db = SessionLocal()
    # Show cases for current user (or all if admin)
    if current_user.role == 'admin':
        cases = db.query(DBCase).order_by(DBCase.updated_at.desc()).all()
    else:
        cases = db.query(DBCase).filter(DBCase.user_id == current_user.id).order_by(DBCase.updated_at.desc()).all()
    
    # Calculate stats
    total_cases = len(cases)
    active_cases = sum(1 for c in cases if c.status == 'active')
    
    # Chart Data: Cases created per day (last 7 days)
    from datetime import datetime, timedelta
    chart_labels = []
    chart_data = []
    today = datetime.now()
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        chart_labels.append(date_str)
        # Count cases created on this day
        count = sum(1 for c in cases if c.created_at and c.created_at.strftime('%Y-%m-%d') == date_str)
        chart_data.append(count)
        
    # Total entities tracked (across user's cases)
    total_addresses = 0
    entity_chart_labels = ["Safe", "Suspicious", "Malicious / Known Threat"]
    entity_chart_data = [0, 0, 0]
    
    if cases:
        case_ids = [c.id for c in cases]
        total_addresses = db.query(Address).filter(Address.case_id.in_(case_ids)).count()
        
        safe_entities = db.query(Address).filter(Address.case_id.in_(case_ids), Address.is_suspicious == False, Address.threat_intel_flag == False).count()
        suspicious_entities = db.query(Address).filter(Address.case_id.in_(case_ids), Address.is_suspicious == True, Address.threat_intel_flag == False).count()
        malicious_entities = db.query(Address).filter(Address.case_id.in_(case_ids), Address.threat_intel_flag == True).count()
        entity_chart_data = [safe_entities, suspicious_entities, malicious_entities]
        
    alerts_count = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    db.close()
    
    return render_template(
        "dashboard.html", 
        cases=cases, 
        active_page="dashboard",
        alerts_count=alerts_count,
        total_cases=total_cases,
        active_cases=active_cases,
        total_addresses=total_addresses,
        chart_labels=chart_labels,
        chart_data=chart_data,
        entity_chart_labels=entity_chart_labels,
        entity_chart_data=entity_chart_data
    )

# Context Processor for Global Template Variables
@app.context_processor
def inject_active_case():
    """Inject active case into all templates"""
    if current_user.is_authenticated:
        active_case = get_active_case()
        return dict(current_case_context=active_case)
    return dict(current_case_context=None)

@app.route("/case/create", methods=["POST"])
@login_required
def create_new_case():
    case_name = request.form.get("case_name")
    description = request.form.get("description")
    
    db = SessionLocal()
    new_case = DBCase(
        case_id=f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        case_name=case_name,
        description=description,
        user_id=current_user.id,
        investigator=current_user.username,
        status="active"
    )
    db.add(new_case)
    db.commit()
    
    # Set as active
    session['active_case_id'] = new_case.id
    flash(f"Case '{case_name}' created and set as active.", "success")
    db.close()
    
    return redirect(url_for('dashboard'))

@app.route("/case/load/<int:case_id>")
@login_required
def load_case(case_id):
    db = SessionLocal()
    case = db.query(DBCase).get(case_id)
    if case:
        session['active_case_id'] = case.id
        flash(f"Switched to case: {case.case_name}", "info")
        return redirect(url_for('investigation'))
    flash("Case not found or access denied.", "error")
    return redirect(url_for('dashboard'))

# --- ADMIN PANEL ROUTES ---
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Administrator access required.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def admin_users():
    db = SessionLocal()
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role", "officer")
            
            if db.query(User).filter((User.username == username) | (User.email == email)).first():
                flash("Username or Email already exists.", "error")
            else:
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                    role=role
                )
                db.add(new_user)
                db.commit()
                flash(f"User {username} created successfully.", "success")
                
        elif action == "edit":
            user_id = request.form.get("user_id")
            user = db.query(User).get(user_id)
            if user:
                user.email = request.form.get("email")
                user.role = request.form.get("role")
                if request.form.get("password"):
                    user.password_hash = generate_password_hash(request.form.get("password"))
                db.commit()
                flash(f"User {user.username} updated.", "success")
                
        elif action == "delete":
            user_id = request.form.get("user_id")
            user = db.query(User).get(user_id)
            if user and user.username != "admin": # prevent deleting main admin
                db.delete(user)
                db.commit()
                flash("User deleted.", "success")
                
    users = db.query(User).order_by(User.id).all()
    db.close()
    return render_template("admin_users.html", users=users)

@app.route("/investigation", methods=["GET", "POST"])
@login_required
def investigation():
    """Investigation Tool - Persistent DB Version"""
    # 1. Load Active Case
    active_case_db = get_active_case()
    if not active_case_db:
        flash("Please select or create a case first.", "warning")
        return redirect(url_for('dashboard'))
        
    db = SessionLocal()
    
    # Context dictionary for template
    context_case = {
        "case_id": active_case_db.case_id,
        "name": active_case_db.case_name,
        "investigator": active_case_db.investigator,
        "address": None,
        "chain": "ethereum",
        "currency": "UNIT",
        "findings": [],
        "transactions": [],
        "summary": None,
        "anomalies": [],
        "threat_intel_results": {}
    }
    
    # Import chain IDs
    from modules.fetchers.eth_live import SUPPORTED_CHAINS
    import re
    
    # Handle New Search (POST)
    if request.method == "POST":
        address = request.form.get("address", "").strip()
        chain_name = request.form.get("chain", "ethereum")
        chain_id = SUPPORTED_CHAINS.get(chain_name.lower(), 1)
        
        # Save focus to session
        session[f"case_focus_{active_case_db.id}"] = {
            "address": address,
            "chain": chain_name,
            "chain_id": chain_id
        }
        
        # 1. Transaction Hash Detection
        is_tx_hash = False
        # EVM, Tron, Bitcoin typically 64 hex chars. 
        # Tron usually starts with block/hash hex but 64 chars is standard.
        # Solana is base58 encoded, length is usually 87-88 chars (up to 90).
        if re.match(r'^(0x)?[a-fA-F0-9]{64}$', address):
             is_tx_hash = True
        elif chain_name in ['solana', 'sol'] and len(address) > 80 and not re.match(r'^[a-fA-F0-9]+$', address):
             # Solana signatures are base58 and quite long (88 chars usually)
             is_tx_hash = True
             
        if is_tx_hash:
            # Strip 0x if present for non-evm just in case, but keep for fetcher to decide
            tx_hash = address
            
            from modules.fetchers.multi_chain import MultiChainFetcher
            tx_details = MultiChainFetcher.fetch_tx_by_hash(chain_name, tx_hash)
            
            if tx_details:
                # Save the hash to the case for persistence
                try:
                    db_tx = db.query(Transaction).filter_by(tx_hash=tx_details['hash']).first()
                    if not db_tx:
                        ts_val = datetime.utcnow()
                        if 'timestamp' in tx_details:
                            try:
                                if isinstance(tx_details['timestamp'], str):
                                    ts_val = datetime.strptime(tx_details['timestamp'], '%Y-%m-%d %H:%M:%S')
                            except: pass
                            
                        db_tx = Transaction(
                            case_id=active_case_db.id,
                            chain_id=chain_id,
                            tx_hash=tx_details['hash'],
                            from_address=tx_details.get('from', 'Unknown'),
                            to_address=tx_details.get('to', 'Unknown'),
                            amount=float(tx_details.get('value', 0)),
                            timestamp=ts_val,
                            block_number=int(tx_details.get('block', 0)) if tx_details.get('block') and str(tx_details.get('block')).isdigit() else None,
                            tx_type='search_target',
                            is_suspicious=False
                        )
                        db.add(db_tx)
                        db.commit()
                except Exception as e:
                    print(f"Failed to persist tx hash: {e}")
                    db.rollback()
                    
                db.close()
                return render_template("transaction.html", tx=tx_details, chain_name=chain_name)
            else:
                flash(f"Could not find transaction details for Hash: {tx_hash} on {chain_name}", "warning")
                db.close()
                return redirect(url_for('investigation'))
            
        # 2. Standard Address Analysis
        if address:
            try:
                # Fetch Data via MultiChainFetcher
                from modules.fetchers.multi_chain import MultiChainFetcher
                txs, counts = MultiChainFetcher.fetch_by_chain(chain_name, address)
                
                # Update/Create Address Record in DB
                addr_record = db.query(Address).filter_by(case_id=active_case_db.id, address=address).first()
                if not addr_record:
                    addr_record = Address(
                        case_id=active_case_db.id,
                        address=address,
                        chain_id=chain_id, # Simplified: assuming 1-to-1 mapping or we need Chain table lookup
                        alias="Target",
                        address_type="suspect"
                    )
                    db.add(addr_record)
                    db.commit() # Commit to get ID
                
                # Save Transactions to DB (Advanced: Bulk Insert)
                # For now, we will rely on fetching live for 'transactions' view to avoid storing 1000s of txs immediately
                # But we SHOULD store the analysis summary
                
                # Run Analysis
                summary, G, source = analyze_live_eth(txs, address, chain_id=chain_id, chain_name=chain_name)
                
                # Update Address Record with Analysis stats
                addr_record.balance = summary.get('final_balance', 0)
                addr_record.total_in = summary.get('total_received', 0)
                addr_record.total_out = summary.get('total_sent', 0)
                addr_record.tx_count = summary.get('total_transactions', 0)
                addr_record.risk_score = summary.get('risk_score', 0)
                addr_record.last_analyzed = datetime.utcnow()
                db.commit()

                # PERSISTENCE: Save Transactions to DB
                try:
                    existing_hashes = {t[0] for t in db.query(Transaction.tx_hash).filter(Transaction.case_id == active_case_db.id).all()}
                    new_txs_db = []
                    
                    for tx in txs:
                        t_hash = tx.get('hash')
                        if not t_hash or t_hash in existing_hashes:
                            continue
                            
                        # Parse timestamp
                        ts_val = datetime.utcnow()
                        if 'timestamp' in tx:
                            try:
                                if isinstance(tx['timestamp'], str):
                                    ts_val = datetime.strptime(tx['timestamp'], '%Y-%m-%d %H:%M:%S')
                                else:
                                    ts_val = tx['timestamp']
                            except:
                                pass
                        
                        # Determine direction/amount for DB storage (simplified)
                        # We store raw from/to/amount.
                        
                        db_tx = Transaction(
                            case_id=active_case_db.id,
                            chain_id=chain_id,
                            tx_hash=t_hash,
                            from_address=tx.get('from'),
                            to_address=tx.get('to'),
                            amount=float(tx.get('value', 0)),
                            timestamp=ts_val,
                            block_number=int(tx.get('block', 0)) if tx.get('block') else None,
                            tx_type=tx.get('type', 'normal'),
                            is_suspicious=False
                        )
                        new_txs_db.append(db_tx)
                        existing_hashes.add(t_hash)
                    
                    if new_txs_db:
                        db.bulk_save_objects(new_txs_db)
                        db.commit()
                        print(f"[Persistence] Saved {len(new_txs_db)} new transactions to DB.")
                        
                except Exception as e_db:
                    print(f"[Persistence Error] Failed to save transactions: {e_db}")
                    db.rollback()

                # Add Finding
                flash(f"Analysis complete for {address} on {chain_name}", "success")
                
            except Exception as e:
                print(f"[ERROR] Logic failed: {e}")
                import traceback
                traceback.print_exc()
                flash(f"Analysis failed: {str(e)}", "error")
    
    # Handle Page Load (GET/Rendering)
    # Check for focused address in session
    focus = session.get(f"case_focus_{active_case_db.id}")
    
    if focus and focus.get("address"):
        address = focus["address"]
        chain_name = focus.get("chain", "ethereum")
        chain_id = focus.get("chain_id", 1)
        
        # Data Loading Strategy: DB First, then API Fallback
        txs = []
        summary = None
        
        # 1. Try DB Load
        addr_record = db.query(Address).filter_by(case_id=active_case_db.id, address=address).first()
        
        if addr_record and addr_record.last_analyzed:
            # Check if we have transactions
            db_txs = db.query(Transaction).filter(
                Transaction.case_id == active_case_db.id,
                (Transaction.from_address == address) | (Transaction.to_address == address)
            ).order_by(Transaction.timestamp.desc()).limit(500).all()
            
            if db_txs:
                print(f"[Persistence] Loading {len(db_txs)} transactions from DB for {address}")
                # Convert DB TXs to format expected by template/analyzer
                for t in db_txs:
                    txs.append({
                        'hash': t.tx_hash,
                        'from': t.from_address,
                        'to': t.to_address,
                        'value': t.amount,
                        'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S') if t.timestamp else '',
                        'block': t.block_number,
                        'chain': chain_name, # or lookup from chain_id
                        'type': t.tx_type
                    })
                
                # Reconstruct summary from Address record
                summary = {
                    'final_balance': addr_record.balance,
                    'total_received': addr_record.total_in,
                    'total_sent': addr_record.total_out,
                    'total_transactions': addr_record.tx_count,
                    'risk_score': addr_record.risk_score,
                    'risk_level': 'HIGH' if addr_record.risk_score >= 80 else 'MEDIUM' if addr_record.risk_score >= 50 else 'LOW'
                }
                # No need to build Graph G for just listing, unless we want the graph view. 
                # For basic dashboard/investigation page, we just need stats and list.
                # If we need G, we call analyze_live_eth with the DB txs.
                
                # Re-run analysis on DB data to get G and fresh context if needed?
                # Yes, safe to re-run analysis logic on memory objects (fast)
                # print("[Persistence] Re-running local analysis on DB data...")
                # summary, G, source = analyze_live_eth(txs, address, chain_id=focus.get('chain_id', 1), chain_name=chain_name)
                
        # 2. Fallback to API if no DB data
        if not txs:
            print(f"[Persistence] No DB data for {address}. Fetching from API...")
            from modules.fetchers.multi_chain import MultiChainFetcher
            txs, counts = MultiChainFetcher.fetch_by_chain(chain_name, address)
            # We don't save here on GET to avoid slow page loads. Explicit "Search" (POST) saves.
        
        # Always run analysis to generate G and formatted summary for template
        summary, G, source = analyze_live_eth(txs, address, chain_id=focus.get('chain_id', 1), chain_name=chain_name)

        context_case["address"] = address
        context_case["chain"] = chain_name
        context_case["transactions"] = txs
        context_case["summary"] = summary
        context_case["currency"] = "ETH" # Simplify or dynamic lookup
        
        # Advanced features
        if ADVANCED_FEATURES_AVAILABLE:
            try:
                from modules.analyzers.advanced_analysis import AddressClustering, ThreatIntelligence
                from modules.analyzers.ml_engine import ml_engine
                
                # 1. Clustering
                context_case["clustering_results"] = AddressClustering.cluster_addresses(txs, address, chain_id=chain_id)
                
                # 2. Threat Intel
                threat_data = ThreatIntelligence.load_threat_data()
                context_case["threat_intel_results"] = ThreatIntelligence.check_address(address, threat_data)
                
                # 3. Anomaly Detection (using ml_engine)
                context_case["anomalies"] = ml_engine.detect_anomalies(txs)
                
                # 4. ML Patterns
                context_case["patterns"] = ml_engine.detect_patterns(txs, address)
                
            except Exception as e:
                print(f"[ADVANCED FEATURES ERROR]: {e}")
                
                import traceback
                traceback.print_exc()

    db.close()
    
    return render_template("investigation.html", 
                         active_page="investigation",
                         current_case=context_case, # Pass dict
                         summary=context_case["summary"], 
                         supported_chains=SUPPORTED_CHAINS,
                         current_chain=context_case.get('chain', 'ethereum'),
                         current_address=context_case.get('address'),
                         fetch_options={'include_internal': True, 'include_token_transfers': True}, # Default options
                         recent_activity=context_case.get('transactions', [])[:5],
                         clustering_results=context_case.get('clustering_results'),
                         threat_intel=context_case.get('threat_intel_results'),
                         anomalies=context_case.get('anomalies'),
                         patterns=context_case.get('patterns'))


# Helper to load case context
def load_case_context():
    """Reconstruct current_case dict from Active Case + Session Focus"""
    active_case_db = get_active_case()
    if not active_case_db:
        return None
        
    current_case = {
        "case_id": active_case_db.case_id,
        "name": active_case_db.case_name,
        "investigator": active_case_db.investigator,
        "address": None,
        "chain": "ethereum",
        "findings": [],
        "transactions": [],
        "summary": None
    }
    
    # Check session focus
    focus_key = f"case_focus_{active_case_db.id}"
    focus = session.get(focus_key)
    
    if focus and focus.get("address"):
        address = focus["address"]
        chain_name = focus.get("chain", "ethereum")
        chain_id = focus.get("chain_id", 1)
        
        # Re-fetch data for context (Hybrid persistence)
        # Ideally this comes from DB, but using fetcher for consistency with current features
        from modules.fetchers.multi_chain import MultiChainFetcher
        txs, counts = MultiChainFetcher.fetch_by_chain(chain_name, address)
        summary, G, source = analyze_live_eth(txs, address, chain_id=chain_id, chain_name=chain_name)
        
        current_case["address"] = address
        current_case["chain"] = chain_name
        current_case["transactions"] = txs
        current_case["summary"] = summary
        current_case["source"] = source
        current_case["counts"] = counts
        current_case["findings"] = [
             f"Target: {address}",
             f"Chain: {chain_name.upper()}",
             f"Transactions: {summary.get('total_transactions', 0)}",
             f"Net Flow: {summary['net_flow']}",
             f"Risk Score: {summary.get('risk_score', 0)}/100"
        ]
        
    return current_case

@app.route("/report", methods=["POST"])
@login_required
def report():
    current_case = load_case_context()
    if not current_case or not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
        
    print("[+] Generating comprehensive forensic report...")
    
    # Generate comprehensive AI analysis
    try:
        analysis_results = generate_comprehensive_analysis(
            current_case["summary"], 
            current_case["findings"]
        )
        current_case["analysis"] = analysis_results
        
        # Extract narrative
        narrative = analysis_results.get("narrative") if isinstance(analysis_results, dict) else analysis_results
        if not narrative or "[Analysis failed" in str(narrative):
            narrative = "Automated analysis unavailable."
    except Exception as e:
        print(f"[!] AI Generation failed: {e}")
        narrative = "AI Analysis Generation Failed."
    
    # Create comprehensive PDF report
    create_pdf(current_case["summary"], current_case["findings"], narrative, current_case.get("source", "Unknown"))
    
    return send_file("exports/forensic_report.pdf", as_attachment=True, 
                    download_name=f"Forensic_Report_{current_case.get('address', 'unknown')[:10]}.pdf")

# GEXF Download Route
@app.route("/downloads/graph.gexf", methods=["GET"])
@login_required
def download_gexf():
    """Download network graph in GEXF format for Gephi"""
    # Use load_case_context to get current address, though GEXF is file-based
    # For now, simplistic check. In future, use case_id in filename.
    current_case = load_case_context()
    if not current_case:
        return "No active case selected.", 404
        
    gexf_path = "exports/graph.gexf"
    
    if os.path.exists(gexf_path):
        return send_file(gexf_path, as_attachment=True, 
                        download_name=f"Transaction_Network_{current_case.get('address', 'network')[:10]}.gexf")
    
    return "Graph file not found. Please run an analysis first.", 404

# Timeline Visualization Route
@app.route("/timeline", methods=["POST"])
@login_required
def timeline():
    """Generate interactive timeline visualization"""
    current_case = load_case_context()
    if not current_case or not current_case["summary"]:
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
@login_required
def sankey():
    """Generate Sankey fund flow diagram"""
    current_case = load_case_context()
    if not current_case or not current_case["summary"]:
        return "No data available. Please perform an analysis first.", 400
    
    address = current_case.get("address")
    sankey_file = create_sankey_diagram(current_case["summary"], address)
    
    if sankey_file and os.path.exists(sankey_file):
        return send_file(sankey_file, as_attachment=True, download_name="sankey.html")
    
    flash("Failed to generate Sankey diagram. Ensure enough transaction data exists.", "error")
    return redirect(url_for('investigation'))

@app.route("/heatmap", methods=["POST"])
@login_required
def heatmap():
    """Generate Heatmap"""
    current_case = load_case_context()
    if not current_case or not current_case["summary"]:
        return "No data available.", 400
        
    address = current_case.get("address")
    txs_data = current_case.get("transactions", [])
    
    heatmap_file = create_heatmap_visualization(txs_data, address)
    
    if heatmap_file and os.path.exists(heatmap_file):
        return send_file(heatmap_file, as_attachment=True, download_name="heatmap.png")
        
    return "Failed to generate heatmap", 500

# Legal/FIR Report Route
@app.route("/legal_report", methods=["POST"])
@login_required
def legal_report():
    """Generate FIR-ready legal report"""
    current_case = load_case_context()
    if not current_case or not current_case["summary"]:
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
@login_required
def list_cases():
    """List all cases"""
    # Filter by user role - Admin sees all, Officer sees own
    db = SessionLocal()
    if current_user.role == 'admin':
        cases = db.query(DBCase).order_by(DBCase.created_at.desc()).all()
    else:
        cases = db.query(DBCase).filter(DBCase.user_id == current_user.id).order_by(DBCase.created_at.desc()).all()
    
    # helper for template
    case_list = [c.to_dict() for c in cases]
    db.close()
    
    current_context = load_case_context()

    return render_template("cases.html", 
                         active_page="cases",
                         cases=case_list,
                         current_case_context=current_context)

@app.route("/cases/create", methods=["POST"])
@login_required
def create_case_route():
    """Create new case (Form submission)"""
    case_name = request.form.get("case_name", "Untitled Case")
    description = request.form.get("description", "")
    investigator = current_user.username
    
    # DB Creation
    import uuid
    new_case = DBCase(
        case_id=str(uuid.uuid4())[:8],
        case_name=case_name,
        description=description,
        investigator=investigator,
        user_id=current_user.id,
        status="active"
    )
    
    db = SessionLocal()
    db.add(new_case)
    db.commit()
    
    # Auto-switch to new case
    session['active_case_id'] = new_case.id # Use DB ID for session
    
    # Initialize session focus
    session[f"case_focus_{new_case.id}"] = {}
    
    db.close()
    
    flash(f"Case '{case_name}' created and set as active.", "success")
    
    return redirect(url_for('list_cases')) # Or redirect to case detail

@app.route("/cases/delete/<case_id>", methods=["POST"])
@login_required
def delete_case_route(case_id):
    """Delete a case"""
    db = SessionLocal()
    # Check permissions
    if current_user.role == 'admin':
        case = db.query(DBCase).filter(DBCase.case_id == case_id).first()
    else:
        case = db.query(DBCase).filter(DBCase.case_id == case_id, DBCase.user_id == current_user.id).first()
        
    if case:
        db.delete(case)
        db.commit()
        if session.get('active_case_id') == int(case_id):
            session.pop('active_case_id', None)
        db.close()
        return jsonify({'success': True, 'message': 'Case deleted'})
    
    db.close()
    return jsonify({'success': False, 'message': 'Case not found or permission denied'}), 404
    return jsonify({'success': False, 'error': 'Failed to delete case'}), 400

@app.route("/cases/switch/<case_id>")
@login_required
def switch_case(case_id):
    """Set active case context"""
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.case_id == case_id).first()
    
    # Check permissions
    if case and (case.user_id == current_user.id or current_user.role == 'admin'):
        session['active_case_id'] = case.id
        flash(f"Switched to case: {case.case_name}", "success")
        db.close()
    else:
        db.close()
        flash("Case not found or permission denied", "error")
        
    return redirect(request.referrer or url_for('list_cases'))

@app.route("/cases/close")
def close_active_case():
    """Close current active case context"""
    session.pop('active_case_id', None)
    flash("Active case closed.", "info")
    return redirect(request.referrer or url_for('list_cases'))

@app.route("/cases/<case_id>")
@login_required
def case_detail(case_id):
    """View case details"""
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.case_id == case_id).first()
    
    if not case or (case.user_id != current_user.id and current_user.role != 'admin'):
        db.close()
        flash("Case not found or permission denied", "error")
        return redirect(url_for('list_cases'))
    
    # Auto-activate the case when viewed so sidebar features display
    session['active_case_id'] = case.id
    
    # helper for template
    case_dict = case.to_dict()
    case_dict['addresses'] = [a.to_dict() for a in case.addresses]
    case_dict['transactions'] = [t.to_dict() for t in case.transactions]
    
    db.close()
    return render_template("case_detail.html", case=case_dict, active_page="cases")

@app.route("/case/<case_id>/add_address", methods=["POST"])
@login_required
def add_address_to_case(case_id):
    """Add address to case"""
    address_str = request.form.get("address")
    tag = request.form.get("tag", "unknown")  # victim, suspect, intermediary, exchange
    
    if not address_str:
         return jsonify({'success': False, 'error': 'Address required'}), 400
         
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.id == case_id).first()
    
    if not case or (case.user_id != current_user.id and current_user.role != 'admin'):
        db.close()
        return jsonify({'success': False, 'error': 'Case not found'}), 404
        
    # Check if address exists in case
    existing = db.query(Address).filter(Address.case_id == case.id, Address.address == address_str).first()
    if existing:
        db.close()
        return jsonify({'success': False, 'message': 'Address already in case'})
        
    new_addr = Address(
        case_id=case.id,
        address=address_str,
        tag=tag,
        chain_id=1 # Default to eth for now, should infer
    )
    db.add(new_addr)
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f"Address {address_str[:10]}... added to case"})

@app.route("/case/<case_id>/add_note", methods=["POST"])
@login_required
def add_note_to_case(case_id):
    """Add note to case"""
    note_content = request.form.get("note", "")
    
    if not note_content:
        return jsonify({'success': False, 'error': "Note content empty"}), 400
        
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.id == case_id).first()
    
    if not case or (case.user_id != current_user.id and current_user.role != 'admin'):
        db.close()
        return jsonify({'success': False, 'error': 'Case not found'}), 404
    
    new_note = CaseNote(
        case_id=case.id,
        content=note_content,
        author=current_user.username
    )
    db.add(new_note)
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': "Note added"})

@app.route("/case/<case_id>/delete_note/<note_id>", methods=["POST"])
@login_required
def delete_note_from_case(case_id, note_id):
    """Delete note from case"""
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.id == case_id).first()
    
    if not case or (case.user_id != current_user.id and current_user.role != 'admin'):
        db.close()
        return jsonify({'success': False, 'error': 'Case not found'}), 404
        
    note = db.query(CaseNote).filter(CaseNote.id == note_id, CaseNote.case_id == case.id).first()
    if note:
        db.delete(note)
        db.commit()
        
    db.close()
    return jsonify({'success': True, 'message': "Note deleted"})

@app.route("/case_board")
@login_required
def case_board():
    """Investigation Board - Sticky Notes and Case Details"""
    active_case_db = get_active_case()
    if not active_case_db:
        flash("Please select a case to view its board.", "warning")
        return redirect(url_for('dashboard'))
        
    db = SessionLocal()
    notes = db.query(CaseNote).filter(CaseNote.case_id == active_case_db.id).order_by(CaseNote.created_at.desc()).all()
    
    notes_data = [{
        "id": n.id,
        "content": n.content,
        "author": n.author,
        "created_at": n.created_at.strftime('%m/%d %H:%M') if n.created_at else ''
    } for n in notes]
    
    db.close()
    
    return render_template("board.html", active_page="board", current_case=active_case_db, notes=notes_data)

@app.route("/case/<case_id>/report", methods=["GET"])
@login_required
def case_report(case_id):
    """Generate case report"""
    db = SessionLocal()
    case = db.query(DBCase).filter(DBCase.id == case_id).first()
    
    if not case or (case.user_id != current_user.id and current_user.role != 'admin'):
        db.close()
        return "Case not found", 404
    
    # Generate comprehensive case report
    report_content = f"""
CASE INVESTIGATION REPORT
========================
Case ID: {case.case_id}
Case Name: {case.case_name}
Investigator: {case.investigator}
Created: {case.created_at}

DESCRIPTION:
{case.description}

ADDRESSES TRACKED:
"""
    
    for addr in case.addresses:
        # Assuming Address model has tag and label or we use defaults
        tag = addr.tag if hasattr(addr, 'tag') else 'unknown'
        # Notes for address? Address model doesn't strictly have 'notes' col unless added, 
        # but let's assume we might just list minimal info or check if we added notes to address. 
        # Check Address model definition earlier... it didn't have notes column, but maybe 'extra_metadata'?
        # For now, just list address and tag.
        report_content += f"\n- {addr.address}\n  Tag: {tag}\n"
    
    report_content += f"\n\nINVESTIGATION NOTES:\n"
    for note in case.notes:
        report_content += f"- [{note.created_at}] {note.author}: {note.content}\n"
    
    db.close()
    return report_content, 200, {'Content-Type': 'text/plain'}




# ==================== BATCH PROCESSING ROUTE (#8) ====================

# ==================== SEED DATA ROUTES ====================
# Legacy explicit seed route removed. Use DB seeding on startup.

# ==================== BATCH PROCESSING ROUTE (#8) ====================

@app.route("/batch", methods=["GET", "POST"])
@login_required
def batch_processing():
    """Batch analyze multiple addresses"""
    from modules.fetchers.eth_live import SUPPORTED_CHAINS
    
    active_case_db = get_active_case()
    if not active_case_db:
        flash("Please select a case to add batch data to.", "warning")
        return redirect(url_for('dashboard'))
        
    results = []
    batch_status = None
    
    if request.method == "POST":
        # Handle CSV Upload
        addresses = []
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
             manual_addrs = [addr.strip() for addr in addresses_input.split('\n') if addr.strip()]
             addresses.extend(manual_addrs)
        
        # Unique addresses
        addresses = list(dict.fromkeys(addresses))
        
        if addresses:
            try:
                print(f"[+] Batch processing {len(addresses)} addresses on {chain_name}...")
                batch_status = {
                    "total": len(addresses),
                    "processed": 0,
                    "results": []
                }
                
                db = SessionLocal()
                
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
                        
                        # Threat check logic...
                        threat = {}
                        if ADVANCED_FEATURES_AVAILABLE:
                             # Simplified for now
                             pass
                        
                        # Save to DB
                        addr_record = db.query(Address).filter_by(case_id=active_case_db.id, address=address).first()
                        if not addr_record:
                            addr_record = Address(
                                case_id=active_case_db.id,
                                address=address,
                                chain=chain_name,
                                address_type="suspect" # Default for batch
                            )
                            db.add(addr_record)
                        
                        addr_record.risk_score = summary.get('risk_score', 0)
                        addr_record.balance = summary.get('final_balance', 0)
                        addr_record.tx_count = summary.get('total_transactions', 0)
                        addr_record.last_analyzed = datetime.utcnow()
                        db.commit()

                        batch_status["results"].append({
                            "address": address,
                            "transactions": counts.get('normal', 0),
                            "risk_score": summary.get('risk_score', 0),
                            "is_flagged": False,
                            "threats": []
                        })
                        
                        batch_status["processed"] += 1
                        print(f"  [{i+1}/{len(addresses)}] {address} - Risk: {summary.get('risk_score', 0)}")
                    
                    except Exception as e:
                        print(f"  [ERROR] {address}: {e}")
                        batch_status["results"].append({
                            "address": address,
                            "error": str(e)
                        })
                
                db.close()
                results = batch_status["results"]
                flash(f"✓ Batch analysis complete: {batch_status['processed']}/{batch_status['total']} addresses processed and saved to case.", "success")
            
            except Exception as e:
                flash(f"Batch processing error: {str(e)}", "error")
    
    return render_template("batch.html", results=results, batch_status=batch_status)


# ==================== CLUSTERING DETAILS ROUTE (#2) ====================

# ==================== TRACING ROUTE ====================
@app.route("/tracing")
@login_required
def tracing():
    """Visual Tracing Interface"""
    current_case = load_case_context()
    if not current_case:
        flash("Please select a case first.", "warning")
        return redirect(url_for('dashboard'))
    current_address = current_case.get("address")
    return render_template("tracing.html", active_page="tracing", current_address=current_address)

@app.route("/investigator")
@login_required
def investigator():
    """Graph Investigator Interface"""
    return render_template("investigator.html", active_page="investigator")

@app.route("/api/trace/<address>")
@login_required
def api_trace(address):
    """Get graph data for Cytoscape - Multi-Chain Support"""
    active_case_db = get_active_case()
    if not active_case_db:
         return jsonify({"error": "No active case"}), 403
         
    from modules.fetchers.multi_chain import MultiChainFetcher
    
    # Get chain from query parameter
    chain_arg = request.args.get('chain', 'ethereum')
    
    # Normalize chain name
    chain_map = {
        '1': 'ethereum',
        '56': 'bsc',
        '137': 'polygon',
        '10': 'optimism',
        '42161': 'arbitrum',
        '8453': 'base',
        '43114': 'avalanche',
        '250': 'fantom',
        '25': 'cronos',
        '1284': 'moonbeam',
        '100': 'gnosis',
        '42220': 'celo',
        '81457': 'blast',
        '59144': 'linea',
        '11155111': 'sepolia',
        # String mappings
        'ethereum': 'ethereum',
        'bitcoin': 'bitcoin',
        'solana': 'solana',
        'tron': 'tron',
        'dogecoin': 'dogecoin',
        'doge': 'dogecoin',
        'xrp': 'xrp',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'optimism': 'optimism',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'avalanche': 'avalanche',
        'fantom': 'fantom',
        'cronos': 'cronos',
        'moonbeam': 'moonbeam',
        'gnosis': 'gnosis',
        'celo': 'celo',
        'blast': 'blast',
        'linea': 'linea',
        'sepolia': 'sepolia'
    }
    
    chain_name = chain_map.get(str(chain_arg).lower(), 'ethereum')
    
    try:
        print(f"[API Trace] Fetching {address} on {chain_name}")
        
        # Fetch transactions using MultiChainFetcher
        txs, counts = MultiChainFetcher.fetch_by_chain(chain_name, address)
        
        # Update Session Focus for Relation Checker & Context
        session[f"case_focus_{active_case_db.id}"] = {
            "address": address,
            "chain": chain_name,
            "chain_id": chain_map.get(chain_name, 1) # Approximate ID
        }
        # In a full persistent system, we would save 'txs' to DB here too
        # For now, we rely on re-fetching in other routes via load_case_context logic using session focus
        
        if not txs:
            return jsonify([{
                'data': {
                    'id': address,
                    'label': address[:8] + '...',
                    'full_address': address,
                    'type': 'root',
                    'risk': 0
                },
                'classes': 'root'
            }])
        
        # Convert to Cytoscape Elements
        elements = []
        node_set = set()
        
        # Currency symbol mapping
        currency_map = {
            'ethereum': 'ETH', 'bitcoin': 'BTC', 'solana': 'SOL',
            'tron': 'TRX', 'dogecoin': 'DOGE', 'bsc': 'BNB',
            'polygon': 'MATIC', 'optimism': 'OP', 'arbitrum': 'ARB',
            'base': 'ETH', 'avalanche': 'AVAX', 'fantom': 'FTM',
            'cronos': 'CRO', 'moonbeam': 'GLMR', 'gnosis': 'GNO',
            'celo': 'CELO', 'blast': 'BLAST', 'linea': 'ETH', 'sepolia': 'ETH', 'xrp': 'XRP'
        }
        currency = currency_map.get(chain_name, 'UNIT')
        
        # Add Root Node
        evm_chains = ['ethereum', 'bsc', 'polygon', 'optimism', 'arbitrum', 'base', 'avalanche', 'fantom', 'cronos', 'moonbeam', 'gnosis', 'celo', 'blast', 'linea', 'sepolia']
        elements.append({
            'data': {
                'id': address.lower() if chain_name in evm_chains else address,
                'label': address[:8] + '...',
                'full_address': address,
                'type': 'root',
                'risk': 0,
                'chain': chain_name
            },
            'classes': 'root'
        })
        node_set.add(address.lower() if chain_name in evm_chains else address)
        
        # Process transactions
        for tx in txs[:200]:  # Limit to 200 for performance
            sender = tx.get('from', 'Unknown')
            receiver = tx.get('to', 'Unknown')
            val = tx.get('value', 0)
            tx_hash = tx.get('hash', '')
            
            # Normalize addresses for EVM chains
            if chain_name in evm_chains:
                sender = sender.lower() if sender != 'Unknown' else sender
                receiver = receiver.lower() if receiver != 'Unknown' else receiver
            
            # Add Sender Node
            if sender and sender != 'Unknown' and sender not in node_set:
                elements.append({
                    'data': {
                        'id': sender,
                        'label': sender[:8] + '...' if len(sender) > 10 else sender,
                        'full_address': sender,
                        'type': 'wallet',
                        'risk': 0,
                        'chain': chain_name
                    }
                })
                node_set.add(sender)
            
            # Add Receiver Node
            if receiver and receiver != 'Unknown' and receiver not in node_set:
                elements.append({
                    'data': {
                        'id': receiver,
                        'label': receiver[:8] + '...' if len(receiver) > 10 else receiver,
                        'full_address': receiver,
                        'type': 'wallet',
                        'risk': 0,
                        'chain': chain_name
                    }
                })
                node_set.add(receiver)
            
            # Add Edge
            if sender != 'Unknown' and receiver != 'Unknown':
                edge_id = f"{sender}_{receiver}_{tx_hash[:8]}"
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': sender,
                        'target': receiver,
                        'label': f"{val:.4f} {currency}" if val > 0 else f"{currency}",
                        'amount': val,
                        'hash': tx_hash,
                        'chain': chain_name
                    }
                })
        
        print(f"[API Trace] Returning {len(elements)} elements ({len(node_set)} nodes)")
        return jsonify(elements)
        
    except Exception as e:
        print(f"[API Trace Error] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@app.route("/api/graph_data")
def api_graph_data():
    """Get graph data for Graph Investigator - Multi-Chain Support"""
    from modules.fetchers.multi_chain import MultiChainFetcher
    
    address = request.args.get('address')
    chain = request.args.get('chain', 'ethereum')
    
    if not address:
        return jsonify({"error": "Missing address parameter"}), 400
    
    try:
        print(f"[API Graph Data] Fetching {address} on {chain}")
        
        # Fetch transactions
        txs, counts = MultiChainFetcher.fetch_by_chain(chain, address)
        
        # Convert to Cytoscape format
        elements = []
        node_set = set()
        
        # Currency mapping
        currency_map = {
            'ethereum': 'ETH', 'bitcoin': 'BTC', 'solana': 'SOL',
            'tron': 'TRX', 'dogecoin': 'DOGE', 'bsc': 'BNB',
            'polygon': 'MATIC', 'optimism': 'OP', 'arbitrum': 'ARB',
            'base': 'ETH', 'avalanche': 'AVAX', 'fantom': 'FTM',
            'cronos': 'CRO', 'moonbeam': 'GLMR', 'gnosis': 'GNO',
            'celo': 'CELO', 'blast': 'BLAST', 'linea': 'ETH', 'sepolia': 'ETH', 'xrp': 'XRP'
        }
        currency = currency_map.get(chain.lower(), 'UNIT')
        
        # Normalize address for EVM chains
        evm_chains = ['ethereum', 'bsc', 'polygon', 'optimism', 'arbitrum', 'base', 'avalanche', 'fantom', 'cronos', 'moonbeam', 'gnosis', 'celo', 'blast', 'linea', 'sepolia']
        is_evm = chain.lower() in evm_chains
        root_id = address.lower() if is_evm else address
        
        # Add root node
        elements.append({
            'group': 'nodes',
            'data': {
                'id': root_id,
                'label': address[:10] + '...',
                'full_address': address,
                'type': 'root',
                'risk': 0
            },
            'classes': 'root'
        })
        node_set.add(root_id)
        
        # Process transactions (limit for performance)
        for tx in txs[:150]:
            sender = tx.get('from', 'Unknown')
            receiver = tx.get('to', 'Unknown')
            val = tx.get('value', 0)
            tx_hash = tx.get('hash', '')
            
            # Normalize for EVM
            if is_evm:
                sender = sender.lower() if sender != 'Unknown' else sender
                receiver = receiver.lower() if receiver != 'Unknown' else receiver
            
            # Add nodes
            if sender and sender != 'Unknown' and sender not in node_set:
                elements.append({
                    'group': 'nodes',
                    'data': {
                        'id': sender,
                        'label': sender[:10] + '...' if len(sender) > 12 else sender,
                        'full_address': sender,
                        'type': 'wallet',
                        'risk': 0
                    }
                })
                node_set.add(sender)
            
            if receiver and receiver != 'Unknown' and receiver not in node_set:
                elements.append({
                    'group': 'nodes',
                    'data': {
                        'id': receiver,
                        'label': receiver[:10] + '...' if len(receiver) > 12 else receiver,
                        'full_address': receiver,
                        'type': 'wallet',
                        'risk': 0
                    }
                })
                node_set.add(receiver)
            
            # Add edge
            if sender != 'Unknown' and receiver != 'Unknown':
                edge_id = f"{sender}_{receiver}_{tx_hash[:10]}"
                elements.append({
                    'group': 'edges',
                    'data': {
                        'id': edge_id,
                        'source': sender,
                        'target': receiver,
                        'label': f"{val:.4f} {currency}" if val > 0 else currency,
                        'amount': val
                    }
                })
        
        print(f"[API Graph Data] Returning {len(node_set)} nodes, {len(elements)} total elements")
        return jsonify({"elements": elements, "stats": {"nodes": len(node_set), "transactions": len(txs)}})
        
    except Exception as e:
        print(f"[API Graph Data Error] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/relations", methods=["GET"])
@login_required
def api_relations():
    """Get transactions between two addresses"""
    source = request.args.get('source', '').strip()
    target = request.args.get('target', '').strip()
    chain = request.args.get('chain', 'ethereum')
    
    if not source or not target:
        return jsonify({"error": "Both source and target addresses required"}), 400
    
    # Get transactions from Database for the active case
    active_case_db = load_case_context()
    
    if not active_case_db:
         return jsonify({"error": "No active case found."}), 400
         
    from modules.core.db_models import Transaction, db_session
    db = db_session()
    
    try:
        # Normalize addresses for comparison
        from modules.utils.helpers import normalize_address
        from modules.fetchers.eth_live import SUPPORTED_CHAINS
        chain_id = SUPPORTED_CHAINS.get(chain.lower(), 1)
        
        source_norm = normalize_address(source, chain_id)
        target_norm = normalize_address(target, chain_id)
        
        # Query DB for transactions between source and target in the current case
        # We need to check both directions: (from=source AND to=target) OR (from=target AND to=source)
        # Note: In DB, EVM addresses should already be stored normalized (lowercased)
        
        txs = db.query(Transaction).filter(
            Transaction.case_id == active_case_db.id,
            (
                ((Transaction.from_address == source_norm) & (Transaction.to_address == target_norm)) |
                ((Transaction.from_address == target_norm) & (Transaction.to_address == source_norm))
            )
        ).all()
        
        relations = []
        for tx in txs:
            relations.append({
                'hash': tx.tx_hash,
                'from': tx.from_address,
                'to': tx.to_address,
                'value': tx.amount,
                'timestamp': tx.timestamp.strftime('%Y-%m-%d %H:%M:%S') if tx.timestamp else 'Unknown',
                'blockNumber': tx.block_number or '',
                'direction': 'outgoing' if tx.from_address == source_norm else 'incoming'
            })
            
    finally:
        db.close()
    
    return jsonify({
        "source": source,
        "target": target,
        "chain": chain,
        "count": len(relations),
        "transactions": relations
    })

# ==================== CLUSTERING DETAILS ROUTE (#2) ====================

@app.route("/clustering")
@login_required
def clustering_details():
    """View cross-address clustering results"""
    current_case = load_case_context()
    clustering = current_case.get("clustering_results", {}) if current_case else {}
    return render_template("clustering.html", clustering=clustering)


# ==================== THREAT INTEL ROUTE (#7) ====================

@app.route("/threat-intel")
@login_required
def threat_intel():
    """View threat intelligence results"""
    current_case = load_case_context()
    if not current_case:
         return redirect(url_for('dashboard'))
    threat = current_case.get("threat_intel_results", {})
    anomalies = current_case.get("anomalies", [])
    return render_template("threat_intel.html", threat=threat, anomalies=anomalies)


# ==================== ANOMALY DETAILS ROUTE (#9) ====================

@app.route("/anomalies")
@login_required
def anomalies():
    """View ML-detected anomalies"""
    current_case = load_case_context()
    anomaly_list = current_case.get("anomalies", []) if current_case else []
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

@app.route("/pathfinder", methods=["GET", "POST"])
@login_required
def pathfinder():
    """Cross-Wallet Pathfinder UI and Engine"""
    from modules.utils.pathfinder import PathFinder
    
    result = None
    if request.method == "POST":
        source = request.form.get("source")
        target = request.form.get("target")
        chain = request.form.get("chain", "ethereum")
        
        if source and target:
            try:
                result = PathFinder.find_path(source, target, chain)
            except Exception as e:
                import traceback
                traceback.print_exc()
                result = {"error": str(e)}
        else:
            result = {"error": "Both Source and Target addresses are required."}
            
    # Need to fetch the global SUPPORTED_CHAINS since this is in app.py
    from modules.fetchers.multi_chain import MultiChainFetcher
    _supported_chains = {
        "EVM Chains (MultiChain)": [
            ("ethereum", "Ethereum Mainnet (ETH)"),
            ("bsc", "BNB Smart Chain (BSC)"),
            ("polygon", "Polygon (MATIC)"),
            ("optimism", "Optimism (OP)"),
            ("arbitrum", "Arbitrum One (ARB)"),
            ("base", "Base (BASE)"),
            ("avalanche", "Avalanche C-Chain (AVAX)"),
            ("fantom", "Fantom (FTM)")
        ],
        "Non-EVM Chains": [
            ("bitcoin", "Bitcoin (BTC)"),
            ("solana", "Solana (SOL)"),
            ("tron", "Tron (TRX)"),
            ("dogecoin", "Dogecoin (DOGE)")
        ]
    }
            
    return render_template("pathfinder.html", active_page="pathfinder", result=result, supported_chains=_supported_chains)

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

@app.route("/export/csv")
@login_required
def export_csv():
    """Export current case transactions to CSV"""
    active_case_db = get_active_case()
    if not active_case_db:
        flash("No active case to export.", "warning")
        return redirect(url_for('dashboard'))
        
    try:
        import pandas as pd
        from io import BytesIO
        
        data = []
        
        # 1. Get DB Transactions (explicitly saved)
        db = SessionLocal()
        transactions = db.query(Transaction).filter_by(case_id=active_case_db.id).all()
        for tx in transactions:
            data.append({
                "Tx Hash": tx.tx_hash,
                "From": tx.from_address,
                "To": tx.to_address,
                "Amount": tx.amount,
                "Fee": tx.fee,
                "Timestamp": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S') if tx.timestamp else '',
                "Block": tx.block_number,
                "Suspicious": "Yes" if tx.is_suspicious else "No",
                "Anomaly Score": tx.anomaly_score
            })
        db.close()
        
        # 2. Add Live Context History (if investigating an address)
        focus_key = f"case_focus_{active_case_db.id}"
        focus = session.get(focus_key)
        if focus and focus.get('address'):
            from modules.fetchers.multi_chain import MultiChainFetcher
            live_txs, _ = MultiChainFetcher.fetch_by_chain(focus['chain'], focus['address'])
            existing_hashes = set(d["Tx Hash"] for d in data)
            
            for tx in live_txs:
                target_hash = tx.get('hash', tx.get('txid', ''))
                if target_hash and target_hash not in existing_hashes:
                    data.append({
                        "Tx Hash": target_hash,
                        "From": tx.get('from', ''),
                        "To": tx.get('to', ''),
                        "Amount": tx.get('value', 0),
                        "Fee": tx.get('fee', 0),
                        "Timestamp": tx.get('timestamp', ''),
                        "Block": tx.get('blockNumber', ''),
                        "Suspicious": "Unknown",
                        "Anomaly Score": 0
                    })
                    existing_hashes.add(target_hash)
            
        df = pd.DataFrame(data)
        
        # Write to BytesIO
        output = BytesIO()
        csv_string = df.to_csv(index=False)
        output.write(csv_string.encode('utf-8'))
        output.seek(0)
        
        filename = f"transactions_{active_case_db.case_id}.csv"
        db.close()
        
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f"Error exporting CSV: {str(e)}", "error")
        return redirect(url_for('investigation'))


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
    app.run(debug=True, port=5000)
