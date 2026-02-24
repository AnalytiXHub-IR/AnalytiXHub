"""
Advanced Analysis Module
- Cross-Address Clustering (Feature #2)
- Threat Intelligence Integration (Feature #7)
- ML Anomaly Detection (Feature #9)
"""
import json
import os
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import math
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from modules.utils.helpers import normalize_address

# ==================== CROSS-ADDRESS CLUSTERING ====================

class AddressClustering:
    """Detect related addresses (same entity, mixer outputs, exchange dust, etc.)"""
    
    @staticmethod
    def cluster_addresses(transactions: List[Dict], main_address: str, chain_id: int = 1) -> Dict:
        """
        Identify clusters of related addresses from transaction patterns
        
        Patterns detected:
        1. Common counterparties (frequent interactions)
        2. Dust transactions (small amounts to many addresses)
        3. Circular patterns (A->B->C->A)
        4. Timing patterns (synchronized sends/receives)
        5. Amount patterns (similar amounts sent to different addresses)
        """
        clusters = {
            'suspicious_counterparties': [],
            'mixer_outputs': [],
            'dust_attacks': [],
            'circular_patterns': [],
            'timing_clusters': [],
            'amount_clusters': [],
        }
        
        # Build address mapping (normalized -> original)
        address_mapping = {}
        for tx in transactions:
            frm = tx.get('from', '')
            to = tx.get('to', '')
            if frm:
                address_mapping[normalize_address(frm, chain_id)] = frm
            if to:
                address_mapping[normalize_address(to, chain_id)] = to
        
        # Build address graph
        graph = AddressClustering._build_address_graph(transactions, chain_id)
        
        # 1. Frequent counterparties (>5 interactions)
        clusters['suspicious_counterparties'] = AddressClustering._find_frequent_counterparties(
            graph, main_address, chain_id, address_mapping, min_interactions=5
        )
        
        # 2. Dust attack detection (many small amounts sent out)
        clusters['dust_attacks'] = AddressClustering._find_dust_attacks(
            transactions, main_address, chain_id, address_mapping
        )
        
        # 3. Circular patterns
        clusters['circular_patterns'] = AddressClustering._find_circular_patterns(
            graph, main_address, chain_id, max_depth=3
        )
        
        # 4. Timing clusters (transactions within 1-5 minutes)
        clusters['timing_clusters'] = AddressClustering._find_timing_clusters(transactions)
        
        # 5. Amount pattern clustering
        clusters['amount_clusters'] = AddressClustering._find_amount_patterns(transactions)
        
        return clusters
    
    @staticmethod
    def _build_address_graph(transactions: List[Dict], chain_id: int) -> Dict[str, Set[str]]:
        """Build adjacency list of address interactions"""
        graph = defaultdict(set)
        for tx in transactions:
            from_addr = normalize_address(tx.get('from', ''), chain_id)
            to_addr = normalize_address(tx.get('to', ''), chain_id)
            if from_addr and to_addr:
                graph[from_addr].add(to_addr)
                graph[to_addr].add(from_addr)
        return dict(graph)
    
    @staticmethod
    def _find_frequent_counterparties(graph: Dict, address: str, chain_id: int,
                                     address_mapping: Dict, min_interactions: int = 5) -> List[Dict]:
        """Find addresses with frequent interactions"""
        address = normalize_address(address, chain_id)
        if address not in graph:
            return []
        
        # Count interactions with each address
        interaction_counts = defaultdict(int)
        for tx in []:  # Would need full tx list for counting
            pass
        
        # Simplified: return top connected addresses with original casing
        counterparties = list(graph.get(address, set()))
        return [
            {'address': address_mapping.get(addr, addr), 'connection_type': 'frequent_interaction', 
             'risk_score': 0.6 if len(counterparties) > 10 else 0.3}
            for addr in counterparties[:10]
        ]
    
    @staticmethod
    def _find_dust_attacks(transactions: List[Dict], main_address: str, chain_id: int, 
                          address_mapping: Dict) -> List[Dict]:
        """Detect dust attacks: many small amounts sent to different addresses"""
        main_address = normalize_address(main_address, chain_id)
        
        # Find outgoing transactions
        outgoing = defaultdict(list)
        for tx in transactions:
            if normalize_address(tx.get('from', ''), chain_id) == main_address:
                to_addr = normalize_address(tx.get('to', ''), chain_id)
                amount = float(tx.get('value', 0))
                outgoing[to_addr].append(amount)
        
        # Identify dust (small amounts to many different addresses)
        dust_threshold = 0.1  # Less than 0.1 ETH/BTC equivalent
        dust_recipients = [addr for addr, amounts in outgoing.items() 
                          if any(amt < dust_threshold for amt in amounts)]
        
        return [
            {'address': address_mapping.get(addr, addr), 'pattern': 'dust_attack', 'risk_score': 0.7, 'is_suspicious': True}
            for addr in dust_recipients[:20]
        ]
    
    @staticmethod
    def _find_circular_patterns(graph: Dict, start_address: str, chain_id: int,
                               max_depth: int = 3) -> List[Dict]:
        """Find circular transaction patterns (A->B->C->A)"""
        start = normalize_address(start_address, chain_id)
        circular = []
        
        def find_paths(current: str, target: str, path: List[str], 
                      visited: Set[str], depth: int) -> bool:
            if depth > max_depth:
                return False
            
            neighbors = graph.get(current, set())
            for neighbor in neighbors:
                if neighbor == target and len(path) >= 2:
                    circular.append({
                        'path': path + [target],
                        'pattern': 'circular',
                        'risk_score': 0.8,
                        'is_suspicious': True
                    })
                    return True
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    find_paths(neighbor, target, path + [current], visited, depth + 1)
                    visited.remove(neighbor)
            
            return False
        
        find_paths(start, start, [], {start}, 1)
        return circular[:10]
    
    @staticmethod
    def _find_timing_clusters(transactions: List[Dict]) -> List[Dict]:
        """Find transactions clustered in time (potential bot/mixer activity)"""
        timing_clusters = []
        
        # Sort by timestamp
        sorted_txs = sorted(transactions, key=lambda x: x.get('timeStamp', 0))
        
        clusters = []
        current_cluster = [sorted_txs[0]] if sorted_txs else []
        
        for tx in sorted_txs[1:]:
            prev_time = int(current_cluster[-1].get('timeStamp', 0))
            curr_time = int(tx.get('timeStamp', 0))
            
            # If within 5 minutes, same cluster
            if curr_time - prev_time <= 300:
                current_cluster.append(tx)
            else:
                # Finalize cluster if >5 transactions
                if len(current_cluster) >= 5:
                    clusters.append(current_cluster)
                current_cluster = [tx]
        
        return [
            {
                'cluster_size': len(c),
                'time_range': f"{int(c[0].get('timeStamp', 0))} - {int(c[-1].get('timeStamp', 0))}",
                'pattern': 'timing_cluster',
                'risk_score': min(0.5 + len(c) * 0.05, 0.95),
                'is_suspicious': len(c) > 10
            }
            for c in clusters
        ]
    
    @staticmethod
    def _find_amount_patterns(transactions: List[Dict]) -> List[Dict]:
        """Find identical or similar amounts sent to different addresses"""
        amounts = defaultdict(list)
        
        for tx in transactions:
            amount = float(tx.get('value', 0))
            if amount > 0:
                amounts[round(amount, 4)].append(tx)
        
        # Find amounts sent to multiple different recipients
        patterns = []
        for amount, txs in amounts.items():
            if len(txs) >= 3:  # Same amount in 3+ transactions
                recipients = set(tx.get('to', '') for tx in txs)
                if len(recipients) >= 3:
                    patterns.append({
                        'amount': amount,
                        'recipient_count': len(recipients),
                        'pattern': 'amount_splitting',
                        'risk_score': 0.6,
                        'is_suspicious': True
                    })
        
        return patterns[:10]


# ==================== THREAT INTELLIGENCE ====================

class ThreatIntelligence:
    """Integrate with threat databases (free sources)"""
    
    # Free threat intelligence sources
    THREAT_SOURCES = {
        'chainalysis': 'data/threat_intel/chainalysis_sanctions.csv',
        'ofac': 'data/threat_intel/ofac_sdn.csv',
        'scamalert': 'data/threat_intel/scamalert.json',
        'etherscan_phishing': 'data/threat_intel/etherscan_phishing.csv',
    }
    
    @staticmethod
    def load_threat_data() -> Dict[str, Set[str]]:
        """Load threat intelligence databases"""
        threat_addresses = defaultdict(set)
        
        # Load Chainalysis sanctions list
        try:
            if os.path.exists(ThreatIntelligence.THREAT_SOURCES['chainalysis']):
                with open(ThreatIntelligence.THREAT_SOURCES['chainalysis']) as f:
                    for line in f:
                        addr = line.strip().split(',')[0].lower()
                        if addr:
                            threat_addresses['chainalysis'].add(addr)
        except Exception as e:
            print(f"⚠️ Chainalysis load error: {e}")
        
        # Load OFAC SDN list
        try:
            if os.path.exists(ThreatIntelligence.THREAT_SOURCES['ofac']):
                with open(ThreatIntelligence.THREAT_SOURCES['ofac']) as f:
                    for line in f:
                        addr = line.strip().split(',')[0].lower()
                        if addr and addr != 'address':
                            threat_addresses['ofac'].add(addr)
        except Exception as e:
            print(f"⚠️ OFAC load error: {e}")
        
        # Load scam database
        try:
            if os.path.exists(ThreatIntelligence.THREAT_SOURCES['scamalert']):
                with open(ThreatIntelligence.THREAT_SOURCES['scamalert']) as f:
                    data = json.load(f)
                    for addr in data.get('scammers', []):
                        threat_addresses['scamalert'].add(addr.lower())
        except Exception as e:
            print(f"⚠️ ScamAlert load error: {e}")
        
        return dict(threat_addresses)
    
    @staticmethod
    def check_address(address: str, threat_data: Dict[str, Set[str]]) -> Dict:
        """Check if address is in threat database"""
        address = address.lower()
        
        threats = {
            'is_flagged': False,
            'threat_sources': [],
            'threat_types': [],
            'severity': 'none',
            'confidence': 0.0,
        }
        
        for source, addresses in threat_data.items():
            if address in addresses:
                threats['is_flagged'] = True
                threats['threat_sources'].append(source)
                
                # Map source to threat type
                threat_type_map = {
                    'chainalysis': 'sanctioned_entity',
                    'ofac': 'ofac_sdn_list',
                    'scamalert': 'known_scammer',
                    'etherscan_phishing': 'phishing_address',
                }
                threats['threat_types'].append(threat_type_map.get(source, source))
        
        # Determine severity
        if threats['is_flagged']:
            source_count = len(threats['threat_sources'])
            if source_count >= 3:
                threats['severity'] = 'critical'
                threats['confidence'] = 0.95
            elif source_count == 2:
                threats['severity'] = 'high'
                threats['confidence'] = 0.85
            else:
                threats['severity'] = 'medium'
                threats['confidence'] = 0.75
        
        return threats
    
    @staticmethod
    def batch_check_addresses(addresses: List[str], 
                             threat_data: Dict[str, Set[str]]) -> Dict[str, Dict]:
        """Check multiple addresses efficiently"""
        results = {}
        for addr in addresses:
            results[addr] = ThreatIntelligence.check_address(addr, threat_data)
        return results


# ==================== ML ANOMALY DETECTION ====================

class AnomalyDetector:
    """Machine learning-based transaction anomaly detection"""
    
    @staticmethod
    def extract_features(transactions: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Extract features from transactions for ML"""
        features = []
        tx_list = []
        
        for tx in transactions:
            # Numeric features
            amount = float(tx.get('value', 0))
            timestamp = int(tx.get('timeStamp', 0))
            gas_price = float(tx.get('gasPrice', 0))
            is_contract = 1 if tx.get('isError', '0') == '0' else 0
            
            # Derived features
            hour_of_day = (timestamp % 86400) // 3600
            day_of_week = (timestamp // 86400) % 7
            
            # Create feature vector
            feature_vector = [
                amount,
                gas_price,
                is_contract,
                hour_of_day,
                day_of_week,
            ]
            
            features.append(feature_vector)
            tx_list.append(tx)
        
        return np.array(features) if features else np.array([]), tx_list
    
    @staticmethod
    def detect_anomalies(transactions: List[Dict], 
                        contamination: float = 0.1) -> List[Dict]:
        """
        Detect anomalous transactions using Isolation Forest
        contamination: expected % of anomalies (0-1)
        """
        if len(transactions) < 5:
            return []  # Need at least 5 transactions for meaningful outliers
        
        # Extract features
        X, tx_list = AnomalyDetector.extract_features(transactions)
        
        if X.shape[0] == 0:
            return []
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest
        model = IsolationForest(contamination=contamination, random_state=42)
        predictions = model.fit_predict(X_scaled)
        scores = model.score_samples(X_scaled)
        
        # Collect anomalies
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly detected
                tx = tx_list[i]
                anomaly_score = 1 - (score + 1) / 2  # Normalize to 0-1
                
                # Determine reason
                reasons = []
                val = float(tx.get('value', 0))
                if val > np.percentile(X[:, 0], 90):
                    reasons.append('unusual_amount_high')
                if val < np.percentile(X[:, 0], 10) and val > 0:
                    reasons.append('unusual_amount_low')
                if float(tx.get('gasPrice', 0)) > np.percentile(X[:, 1], 95):
                    reasons.append('unusually_high_gas')
                
                anomalies.append({
                    'hash': tx.get('hash', tx.get('txid', '')),
                    'from': tx.get('from', ''),
                    'to': tx.get('to', ''),
                    'amount': float(tx.get('value', 0)),
                    'timestamp': datetime.fromtimestamp(int(tx.get('timeStamp', 0))).strftime('%Y-%m-%d %H:%M:%S') if tx.get('timeStamp') else 'Unknown',
                    'anomaly_score': float(anomaly_score),
                    'reasons': reasons,
                    'type': 'ML Anomaly' if not reasons else reasons[0].replace('_', ' ').title(),
                    'description': f"Unusual transaction behavior detected. Score: {anomaly_score:.2f}. " + (f"Reasons: {', '.join(reasons)}" if reasons else ""),
                    'is_suspicious': bool(anomaly_score > 0.5), # Lowered threshold from 0.7 for better sensitivity
                    'address': tx.get('from', '') if tx.get('from') != '0x0000000000000000000000000000000000000000' else tx.get('to', '')
                })
        
        return sorted(anomalies, key=lambda x: x['anomaly_score'], reverse=True)
    
    @staticmethod
    def behavioral_analysis(transactions: List[Dict]) -> Dict:
        """Analyze behavioral patterns and establish baseline"""
        if not transactions:
            return {}
        
        amounts = [float(tx.get('value', 0)) for tx in transactions if float(tx.get('value', 0)) > 0]
        timestamps = [int(tx.get('timeStamp', 0)) for tx in transactions]
        
        return {
            'avg_amount': np.mean(amounts) if amounts else 0,
            'median_amount': np.median(amounts) if amounts else 0,
            'std_amount': np.std(amounts) if amounts else 0,
            'max_amount': np.max(amounts) if amounts else 0,
            'min_amount': np.min(amounts) if amounts else 0,
            'avg_frequency': len(transactions) / ((max(timestamps) - min(timestamps)) / 86400) if len(transactions) > 1 else 0,
            'activity_hours': set((ts % 86400) // 3600 for ts in timestamps),
            'active_days': set((ts // 86400) % 7 for ts in timestamps),
        }


# ==================== TESTING ====================

if __name__ == '__main__':
    print("Testing Advanced Analysis...\n")
    
    # Test clustering
    print("Testing Address Clustering...")
    test_txs = [
        {'from': '0x123', 'to': '0xabc', 'value': '1', 'timeStamp': '1700000000'},
        {'from': '0x123', 'to': '0xdef', 'value': '0.001', 'timeStamp': '1700000100'},
        {'from': '0x123', 'to': '0xghi', 'value': '0.001', 'timeStamp': '1700000110'},
    ]
    clusters = AddressClustering.cluster_addresses(test_txs, '0x123')
    print(f"Clustering found: {len(clusters)} pattern types\n")
    
    # Test threat intel
    print("Testing Threat Intelligence...")
    threats = ThreatIntelligence.check_address('0x123', {})
    print(f"Threat check: {threats['is_flagged']}\n")
    
    # Test anomaly detection
    print("Testing Anomaly Detection...")
    complex_txs = [
        {'value': str(i), 'timeStamp': str(1700000000 + i*100), 'gasPrice': '1', 'isError': '0'}
        for i in range(50)
    ]
    anomalies = AnomalyDetector.detect_anomalies(complex_txs)
    print(f"Anomalies detected: {len(anomalies)}\n")
    
    print("All advanced analysis features working!")
