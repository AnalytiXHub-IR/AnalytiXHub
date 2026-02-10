import pandas as pd
import networkx as nx
from datetime import datetime
from collections import Counter, defaultdict

# Enhanced entity database
KNOWN_ENTITIES = {
    # Individuals
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045": {"name": "Vitalik Buterin", "type": "Individual", "risk": "LOW"},
    
    # Exchanges
    "0x28C6c06298d514Db089934071355E5743bf21d60": {"name": "Binance Hot Wallet", "type": "Exchange", "risk": "LOW"},
    "0x77696bb39917C91A0c3908D577d5e322095425cA": {"name": "Coinbase Hot Wallet", "type": "Exchange", "risk": "LOW"},
    "0x1111111111111111111111111111111111111111": {"name": "Kraken Exchange", "type": "Exchange", "risk": "LOW"},
    
    # Ransomware - WannaCry
    "0x8626f6940e2eb28930df1c8e74e7b6aaf002e33e": {"name": "WannaCry Ransomware Payments", "type": "Ransomware", "risk": "CRITICAL"},
    "0x394cff924caf8598b022503b023d87b96f5bd8e5": {"name": "WannaCry Bitcoin Tumbler", "type": "Ransomware", "risk": "CRITICAL"},
    "0xa4EDE3b20d41db0f0f01c5aE2cBc7f54Dc22e94f": {"name": "WannaCry Victims' Refund Address", "type": "Ransomware", "risk": "CRITICAL"},
    
    # Mixing/Tumbling Services
    "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc": {"name": "Tornado Cash Router", "type": "Mixer", "risk": "CRITICAL"},
    "0xd4b88df4d29f5cdf15910dcb5bef341d57227f59": {"name": "Coin Join Service", "type": "Mixer", "risk": "HIGH"},
    
    # Bridges
    "0x098B716B8Aaf21512996dC57EB0615e2383E2f96": {"name": "Ronin Bridge", "type": "Bridge", "risk": "MEDIUM"},
    
    # DeFi Protocols
    "0x1f98431c8ad98523631ae4a59f267346ea31f984": {"name": "Uniswap V3", "type": "DEX", "risk": "LOW"},
    "0x68b3465833fb72B5A828cCEd3294e3B6b3214313": {"name": "Uniswap Router", "type": "DEX", "risk": "LOW"},
    
    # Known Scam Wallets
    "0x0000000000000000000000000000000000000000": {"name": "Null Address", "type": "System", "risk": "MEDIUM"},
}

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

def identify_entity_type(address, transactions):
    """Advanced entity type identification based on transaction patterns"""
    if address in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[address]
    
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

    return risk_score, risk_factors

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

def analyze_live_eth(txlist, root_address, start_date=None, end_date=None, chain_id=1, chain_name="ethereum"):
    """Enhanced analysis with pattern detection and risk scoring.
    
    Args:
        txlist: List of transactions
        root_address: Address being analyzed
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        chain_id: Blockchain chain ID (1=Ethereum, 56=BSC, etc.)
        chain_name: Human-readable chain name
    """
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
            ts = float(tx.get("timeStamp", 0))
        except:
            ts = 0.0
            
        if not (start_ts <= ts <= end_ts):
            continue

        filtered_txs.append(tx)
        
        frm = tx.get("from")
        to = tx.get("to")
        
        try:
            val = float(tx.get("value", 0)) / 1e18
        except:
            val = 0.0
        
        transaction_values.append(val)
        
        frm_label = KNOWN_ENTITIES.get(frm, frm[:10] + "...")
        to_label = KNOWN_ENTITIES.get(to, to[:10] + "...")

        G.add_edge(frm, to, value=val, label=f"{val:.2f} ETH")

        if to and to.lower() == root_address.lower():
            total_in += val
            all_victims.append(frm)
            incoming_addresses[frm] += val
        elif frm and frm.lower() == root_address.lower():
            total_out += val
            all_suspects.append(to)
            outgoing_addresses[to] += val
            
            if to in KNOWN_ENTITIES:
                cash_out_points.append(f"{val:.2f} ETH -> {KNOWN_ENTITIES[to]}")

    # Get top victims and suspects
    top_victims = [v for v, _ in Counter(all_victims).most_common(5)]
    top_suspects = [s for s, _ in Counter(all_suspects).most_common(5)]
    
    # Top by value
    top_victims_by_value = sorted(incoming_addresses.items(), key=lambda x: x[1], reverse=True)[:5]
    top_suspects_by_value = sorted(outgoing_addresses.items(), key=lambda x: x[1], reverse=True)[:5]

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
    entity_info = identify_entity_type(root_address, filtered_txs)

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
        "top_suspects": top_suspects_by_value,
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
        "chain_id": chain_id,  # NEW: Chain identifier
        "chain_name": chain_name,  # NEW: Human-readable chain name
    }

    return summary, G, "Live Blockchain Data"

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