import pandas as pd
import networkx as nx
from datetime import datetime
from collections import Counter, defaultdict
from db_models import SessionLocal, ThreatIntel, Address, Transaction, Case
from sqlalchemy.orm import Session

# Enhanced entity type mapping
ENTITY_TYPES = {
    "Exchange": "CEX - Centralized Exchange",
    "DEX": "Decentralized Exchange",
    "Mixer": "⚠️ Mixing Service - HIGH RISK",
    "Bridge": "Cross-chain Bridge",
    "DeFi": "DeFi Protocol",
    "Staking": "Staking Service",
    "Individual": "Individual Account",
    "Smart_Contract": "Smart Contract",
    "System": "System Address"
}

def save_transactions(db: Session, txs: list, chain_id: int, case_id: int = None):
    """Bulk save transactions to DB and link to Case"""
    if not txs: return
    
    # Get existing hashes to check for updates
    hashes = [tx.get('hash') for tx in txs if tx.get('hash')]
    if not hashes: return
    
    existing_objs = db.query(Transaction).filter(Transaction.tx_hash.in_(hashes)).all()
    existing_map = {t.tx_hash: t for t in existing_objs}
    
    new_txs = []
    for tx in txs:
        tx_hash = tx.get('hash')
        if not tx_hash: continue

        # If existing, update case_id to current case (Steal/re-assign for visibility)
        if tx_hash in existing_map:
            if case_id:
                existing_map[tx_hash].case_id = case_id
            continue
            
        try:
            val = float(tx.get("value", 0)) / 1e18
        except: val = 0.0
        
        try:
            ts = float(tx.get("timeStamp", 0))
            dt = datetime.fromtimestamp(ts)
        except: dt = datetime.utcnow()
        
        try:
            gas_used = float(tx.get("gasUsed", 0))
            gas_price = float(tx.get("gasPrice", 0))
            fee = (gas_used * gas_price) / 1e18
        except: fee = 0.0
        
        # Determine tx_type logic (simple)
        tx_type = "normal"
        if tx.get("input") and len(tx.get("input")) > 2:
            tx_type = "contract_interaction"
        if tx.get("value") == "0" and tx.get("input") == "0x":
            tx_type = "token_transfer" # Primitive guess
            
        new_tx = Transaction(
            tx_hash=tx_hash,
            chain_id=int(chain_id),
            block_number=int(tx.get('blockNumber', 0)),
            timestamp=dt,
            from_address=tx.get('from'),
            to_address=tx.get('to'),
            amount=val,
            fee=fee,
            tx_type=tx_type,
            case_id=case_id # Link to case
        )
        new_txs.append(new_tx)
    
    try:
        if new_txs:
            db.bulk_save_objects(new_txs)
        db.commit()
    except Exception as e:
        print(f"Db Save Error: {e}")
        db.rollback()

def get_entity_info(address, db: Session):
    """Resolve entity info from Database"""
    if not address: return None
    
    # Check ThreatIntel
    ti = db.query(ThreatIntel).filter_by(address=address).first()
    if ti:
        return {
            "name": ti.entity_name,
            "type": ti.entity_type,
            "risk": "CRITICAL" if ti.confidence > 0.9 else "HIGH" if ti.confidence > 0.7 else "LOW"
        }
        
    # Check Address (User labeled)
    addr = db.query(Address).filter_by(address=address).first()
    if addr and addr.label:
        return {
            "name": addr.label,
            "type": addr.address_type,
            "risk": "HIGH" if addr.is_suspicious else "LOW"
        }
        
    return None

def identify_entity_type(address, transactions, db: Session = None):
    """Advanced entity type identification based on transaction patterns"""
    if db:
        info = get_entity_info(address, db)
        if info: return info
    
    # Analyze transaction patterns to infer type
    incoming = len([tx for tx in transactions if tx.get("to", "").lower() == address.lower()])
    outgoing = len([tx for tx in transactions if tx.get("from", "").lower() == address.lower()])
    
    if incoming > outgoing * 5:
        return {"name": "Possible Exchange/Aggregator", "type": "Exchange", "risk": "LOW", "confidence": "MEDIUM"}
    
    if incoming > outgoing * 2:
        return {"name": "Possible Mixer Service", "type": "Mixer", "risk": "HIGH", "confidence": "MEDIUM"}
    
    if incoming == 0 and outgoing > 20:
        return {"name": "Distribution Wallet", "type": "Smart_Contract", "risk": "MEDIUM", "confidence": "MEDIUM"}
    
    return {"name": "Unknown Address", "type": "Unknown", "risk": "UNKNOWN", "confidence": "LOW"}

def get_safe_timestamp(date_str, default_val):
    """Safely converts string date to timestamp, handling Windows limits."""
    if not date_str:
        return default_val
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.year < 1970: 
            return 0.0
        return dt.timestamp()
    except (ValueError, OSError):
        return default_val

def detect_patterns(txlist, root_address):
    """Detects suspicious transaction patterns."""
    patterns = {
        "rapid_succession": False,
        "round_amounts": [],
        "suspicious_destinations": [],
        "dust_transactions": [],
        "high_frequency_wallet": False,
        "mixing_service_suspicion": False,
        "consolidation_pattern": False,
        "layering_pattern": False
    }
    
    if not txlist:
        return patterns
    
    # Check for rapid succession (multiple txs within short time)
    sorted_txs = sorted(txlist, key=lambda x: float(x.get("timeStamp", 0)))
    timestamps = [float(tx.get("timeStamp", 0)) for tx in sorted_txs]
    
    if len(timestamps) > 2:
        time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        rapid_count = sum(1 for diff in time_diffs if 0 < diff < 60)  # Within 1 minute
        if rapid_count > len(time_diffs) * 0.3:
            patterns["rapid_succession"] = True
    
    # Check for round amounts (suspicious pattern)
    for tx in txlist:
        try:
            val = float(tx.get("value", 0)) / 1e18
            if val > 0 and val == int(val):  # Round number
                patterns["round_amounts"].append(val)
        except:
            pass
    
    # Check for dust transactions (very small amounts)
    for tx in txlist:
        try:
            val = float(tx.get("value", 0)) / 1e18
            if 0 < val < 0.01:  # Less than 0.01 ETH
                patterns["dust_transactions"].append(round(val, 6))
        except:
            pass
    
    # High frequency check
    if len(txlist) > 50:
        patterns["high_frequency_wallet"] = True
    
    # Mixing service suspicion (many inputs, few outputs)
    incoming = sum(1 for tx in txlist if tx.get("to", "").lower() == root_address.lower())
    outgoing = sum(1 for tx in txlist if tx.get("from", "").lower() == root_address.lower())
    if incoming > outgoing * 2:
        patterns["mixing_service_suspicion"] = True
    
    # Consolidation pattern (many small inputs, large output)
    input_amounts = [float(tx.get("value", 0)) / 1e18 for tx in txlist 
                     if tx.get("to", "").lower() == root_address.lower()]
    output_amounts = [float(tx.get("value", 0)) / 1e18 for tx in txlist 
                      if tx.get("from", "").lower() == root_address.lower()]
    
    if input_amounts and output_amounts:
        avg_input = sum(input_amounts) / len(input_amounts) if input_amounts else 0
        max_output = max(output_amounts) if output_amounts else 0
        if avg_input > 0 and max_output > avg_input * 10:
            patterns["consolidation_pattern"] = True
    
    # Layering pattern (many intermediate transfers)
    if len(txlist) > 20 and len(set(tx.get("from") for tx in txlist)) > len(set(tx.get("to") for tx in txlist)):
        patterns["layering_pattern"] = True
    
    return patterns

def calculate_confidence_score(summary, patterns, risk_score):
    """Calculate confidence level (0-100%) that assessment is accurate"""
    confidence = 50  # Base confidence
    
    # More data = more confidence
    if summary.get("total_transactions", 0) > 100:
        confidence += 20
    elif summary.get("total_transactions", 0) > 50:
        confidence += 10
    
    # More unique parties = more confidence
    unique_parties = summary.get("unique_senders", 0) + summary.get("unique_receivers", 0)
    if unique_parties > 30:
        confidence += 15
    elif unique_parties > 15:
        confidence += 8
    
    # Patterns increase confidence
    pattern_count = sum(1 for v in patterns.values() if isinstance(v, bool) and v)
    confidence += min(pattern_count * 3, 20)
    
    # Cap at 100
    confidence = min(confidence, 100)
    
    return confidence

def calculate_risk_score(patterns, summary):
    """Calculates risk score based on detected patterns."""
    risk_score = 0
    risk_factors = []
    
    if patterns["rapid_succession"]:
        risk_score += 20
        risk_factors.append("Rapid succession of transactions")
    
    if patterns["high_frequency_wallet"]:
        risk_score += 15
        risk_factors.append("High frequency transaction wallet")
    
    if patterns["mixing_service_suspicion"]:
        risk_score += 25
        risk_factors.append("Possible mixing service behavior")
    
    if patterns["consolidation_pattern"]:
        risk_score += 20
        risk_factors.append("Consolidation pattern detected")
    
    if patterns["layering_pattern"]:
        risk_score += 18
        risk_factors.append("Layering pattern detected (AML concern)")
    
    if len(patterns["dust_transactions"]) > 5:
        risk_score += 15
        risk_factors.append("Multiple dust transactions (potential obfuscation)")
    
    total_txs = summary.get("total_transactions", 0)
    if total_txs > 0 and len(patterns["round_amounts"]) > total_txs * 0.3:
        risk_score += 10
        risk_factors.append("High proportion of round amount transactions")
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    return risk_score, risk_factors

def analyze_live_chain(address, chain="ethereum", api_keys=None, case_id=None):
    """
    Unified analysis function for any supported chain.
    """
    from multi_chain import MultiChainFetcher
    
    fetcher = MultiChainFetcher(api_keys)
    txs, counts = fetcher.fetch_transactions(chain, address)
    
    # Map chain name to ID for DB
    chain_map = {
        'ethereum': 1, 'bitcoin': 2, 'solana': 3, 'tron': 4,
        'bsc': 56, 'polygon': 137, 'optimism': 10, 'arbitrum': 42161
    }
    chain_id = chain_map.get(chain.lower(), 999)
    
    # Run analysis (reuses the robust logic from analyze_live_eth, but generalized)
    # The existing analyze_live_eth logic is actually quite generic IF tx format is standard.
    # MultiChainFetcher normalizes txs to have 'from', 'to', 'value', 'timeStamp', 'hash'.
    
    return analyze_live_eth(txs, address, chain_id=chain_id, chain_name=chain, case_id=case_id)

def analyze_live_eth(txlist, root_address, start_date=None, end_date=None, chain_id=1, chain_name="ethereum", case_id=None):
    """Enhanced analysis with pattern detection, risk scoring, and DB persistence."""
    # Persist transactions to DB first
    db = SessionLocal()
    try:
        save_transactions(db, txlist, chain_id, case_id=case_id)
    except Exception as e:
        print(f"Error saving transactions: {e}")
    finally:
        db.close()

    db = SessionLocal()
    try:
        G = nx.DiGraph()
        filtered_txs = []
        
        start_ts = get_safe_timestamp(start_date, 0.0)
        end_ts = get_safe_timestamp(end_date, 4102444800.0)

        total_in = 0.0
        total_out = 0.0
        cash_out_points = []
        all_victims = []
        all_suspects = []
        transaction_values = []
        incoming_addresses = defaultdict(float)
        outgoing_addresses = defaultdict(float)

        for tx in txlist:
            try:
                # Handle different timestamp formats (BTC/Solana might return seconds, others ms)
                ts_raw = tx.get("timeStamp", 0)
                ts = float(ts_raw)
                # Auto-detect ms vs seconds
                if ts > 1000000000000: ts /= 1000
            except:
                ts = 0.0
                
            if not (start_ts <= ts <= end_ts):
                continue

            filtered_txs.append(tx)
            
            # Normalize address case for comparison
            frm = str(tx.get("from")).lower() if tx.get("from") else "unknown"
            to = str(tx.get("to")).lower() if tx.get("to") else "unknown"
            
            try:
                val = float(tx.get("value", 0))
                # ETH/EVMs use 1e18, BTC 1e8, SOL 1e9. 
                # MultiChainFetcher ALREADY normalized value to human readable units?
                # Let's check MultiChainFetcher. Yes, it does.
                # But analyze_live_eth was expecting Raw Wei and dividing by 1e18.
                # We need to detect if it's already normalized or not.
                # HACK: If value is huge (> 1e9), assume Wei/Satoshis. If small, assume ETH/BTC.
                if val > 1_000_000_000: # It's probably Wei/Lamports
                     if chain_name == 'solana': val /= 1e9
                     elif chain_name == 'bitcoin': val /= 1e8
                     else: val /= 1e18
            except:
                val = 0.0
            
            transaction_values.append(val)
            
            # Entity Resolution from DB
            frm_info = get_entity_info(frm, db)
            to_info = get_entity_info(to, db)
            
            frm_label = frm_info['name'] if frm_info else frm[:10] + "..."
            to_label = to_info['name'] if to_info else to[:10] + "..."

            G.add_edge(frm, to, value=val, label=f"{val:.4f} {chain_name[:3].upper()}")

            if to.lower() == root_address.lower():
                total_in += val
                all_victims.append(frm)
                incoming_addresses[frm] += val
            elif frm.lower() == root_address.lower():
                total_out += val
                all_suspects.append(to)
                outgoing_addresses[to] += val
                
                if to_info:
                    cash_out_points.append(f"{val:.2f} -> {to_info['name']}")

        # Get top victims and suspects
        top_victims = [v for v, _ in Counter(all_victims).most_common(5)]
        top_suspects = [s for s, _ in Counter(all_suspects).most_common(5)]
        
        # Top by value
        top_victims_by_value = sorted(incoming_addresses.items(), key=lambda x: x[1], reverse=True)[:5]
        top_suspects_by_by_value = sorted(outgoing_addresses.items(), key=lambda x: x[1], reverse=True)[:5]

        # Detect patterns
        patterns = detect_patterns(filtered_txs, root_address)
        risk_score, risk_factors = calculate_risk_score(patterns, {
            "total_transactions": len(filtered_txs)
        })
        
        # Calculate confidence score
        temp_summary = {"total_transactions": len(filtered_txs), 
                        "unique_senders": len(set(tx.get("from") for tx in filtered_txs if tx.get("from"))),
                        "unique_receivers": len(set(tx.get("to") for tx in filtered_txs if tx.get("to")))}
        confidence_score = calculate_confidence_score(temp_summary, patterns, risk_score)

        # Calculate statistics
        avg_transaction = sum(transaction_values) / len(transaction_values) if transaction_values else 0
        median_transaction = sorted(transaction_values)[len(transaction_values)//2] if transaction_values else 0
        max_transaction = max(transaction_values) if transaction_values else 0
        
        # Entity type identification
        entity_info = identify_entity_type(root_address, filtered_txs, db)

        summary = {
            "total_transactions": len(filtered_txs),
            "total_volume_in": float(round(total_in, 4)) if total_in else 0.0,
            "total_volume_out": float(round(total_out, 4)) if total_out else 0.0,
            "net_flow": float(round(total_in - total_out, 4)) if (total_in or total_out) else 0.0,
            "unique_senders": len(set(tx.get("from") for tx in filtered_txs if tx.get("from"))),
            "unique_receivers": len(set(tx.get("to") for tx in filtered_txs if tx.get("to"))),
            "avg_transaction_value": float(round(avg_transaction, 4)) if avg_transaction else 0.0,
            "median_transaction_value": float(round(median_transaction, 4)) if median_transaction else 0.0,
            "max_transaction_value": round(max_transaction, 4),
            "top_victims": top_victims_by_value,
            "top_suspects": top_suspects_by_by_value,
            "cash_out_points": cash_out_points,
            "patterns": patterns,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "confidence_score": confidence_score,
            "entity_info": entity_info,
            "incoming_addresses": dict(incoming_addresses),
            "outgoing_addresses": dict(outgoing_addresses),
            "start_date": start_date or "All Time",
            "end_date": end_date or "Present",
            "chain_id": chain_id,
            "chain_name": chain_name,
        }
        
    # ... existing code ...
    
        # ---------------------------------------------------------
        # BREADCRUMBS INTEGRATION (Enrichment)
        # ---------------------------------------------------------
        try:
            from breadcrumbs_client import BreadcrumbsClient
            bc = BreadcrumbsClient()
            
            # 1. Get Risk for Root Address
            root_risk = bc.get_risk(root_address, chain=chain_name)
            if root_risk:
                # Update summary with rich data
                summary["risk_score"] = max(summary.get("risk_score", 0), root_risk.get("risk_score", 0) * 100)
                if root_risk.get("labels"):
                    summary["risk_factors"].extend([f"Breadcrumbs: {l}" for l in root_risk.get("labels")])
            
            # 2. Enrich Graph Nodes
            # We can fetch neighbors via Breadcrumbs to find hidden connections not collecting via simple tx list
            # For now, let's just label existing nodes if they are high risk
            # Optimize: Batch check? Breadcrumbs API seems single address.
            # We will check only top suspects/victims to save API calls/Time
            
            nodes_to_check = [n for n in G.nodes if n != root_address]
            # Sort by volume to prioritize
            # (This logic would require querying G edges, which is expensive if large)
            
            # For prototype: Check root address neighbors in G with high value
            # Or better: Use Breadcrumbs to EXPAND the graph
            
            bc_txs = bc.get_transactions(root_address, chain=chain_name, limit=5)
            if bc_txs and "transactions" in bc_txs:
                for btx in bc_txs["transactions"]:
                    other = btx.get("from") if btx.get("to") == root_address else btx.get("to")
                    val = float(btx.get("value", 0))
                    label = btx.get("counterparty_label", "Unknown")
                   
                    # Add to Graph if not exists
                    if not G.has_edge(btx["from"], btx["to"]):
                        G.add_edge(btx["from"], btx["to"], value=val, label=f"{val:.4f} (BC)")
                       
                    # Add Metadata
                    if G.has_node(other):
                        nx.set_node_attributes(G, {other: {"label": label, "type": "enriched"}})

        except Exception as e:
            print(f"[Analyzer] Breadcrumbs Enrichment Failed: {e}")

    # ---------------------------------------------------------

        return summary, G, f"Live {chain_name.title()} Data"

    finally:
        db.close()

def analyze_multiple_addresses(addresses, api_key, start_date=None, end_date=None):
    """Track funds across multiple addresses"""
    from eth_live import fetch_eth_address
    
    combined_summary = {
        "addresses": {},
        "network_graph": nx.DiGraph(),
        "fund_flow": [],  # [{from, to, amount, hops}]
        "total_addresses": len(addresses),
        "total_value_tracked": 0
    }
    
    address_data = {}
    for addr in addresses:
        try:
            txs = fetch_eth_address(addr, api_key, include_internal=True, include_token_transfers=True)
            summary, G, _ = analyze_live_eth(txs, addr, start_date, end_date)
            address_data[addr] = {
                "summary": summary,
                "graph": G
            }
            combined_summary["addresses"][addr] = summary
            combined_summary["network_graph"] = nx.compose(combined_summary["network_graph"], G)
            combined_summary["total_value_tracked"] += summary.get("total_volume_in", 0)
        except Exception as e:
            print(f"[ERROR] Analyzing {addr}: {e}")
    
    return combined_summary

def analyze_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        G = nx.DiGraph()
        for _, r in df.iterrows():
            G.add_edge(r["from"], r["to"], value=r["value"])
        
        return {
            "total_transactions": len(df),
            "total_volume_in": 0, "total_volume_out": 0, "net_flow": 0,
            "unique_senders": 0, "unique_receivers": 0,
            "cash_out_points": [],
            "confidence_score": 0,
            "entity_info": {}
        }, G, "Reference Dataset (Fallback)"
    except:
        return {}, nx.DiGraph(), "Error"