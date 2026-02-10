"""
Taint Analysis & Fund Flow Tracking
Trace stolen funds through mixers, bridges, and swaps
"""

import networkx as nx
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

class TaintAnalyzer:
    """
    Trace fund flow through blockchain
    Tracks stolen funds through:
    - Mixing services (Tornado Cash, Coin Join, etc.)
    - Bridges (Ronin, Polygon Bridge, etc.)
    - DEX/AMM swaps
    - CEX deposits
    """
    
    # Known mixer/tumbler addresses
    KNOWN_MIXERS = {
        'tornado_cash_router': '0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc',
        'coin_join': '0xd4b88df4d29f5cdf15910dcb5bef341d57227f59',
        'mixing_service': '0x1234567890123456789012345678901234567890',
    }
    
    # Known bridges
    KNOWN_BRIDGES = {
        'polygon_bridge': '0x098B716B8Aaf21512996dC57EB0615e2383E2f96',
        'arbitrum_bridge': '0xC119BC18c7d19b5ef8E330a5D9cBBB16f85B46F2',
        'optimism_bridge': '0x4200000000000000000000000000000000000010',
    }
    
    # Known CEX deposit addresses (Binance, Kraken, etc.)
    KNOWN_CEXES = {
        'binance_deposit_1': '0x28C6c06298d514Db089934071355E5743bf21d60',
        'coinbase_deposit_1': '0x77696bb39917C91A0c3908D577d5e322095425cA',
        'kraken_deposit_1': '0x1111111111111111111111111111111111111111',
    }
    
    def __init__(self, transactions: List[Dict]):
        """Initialize with transaction data"""
        self.transactions = transactions
        self.graph = self._build_transaction_graph()
        self.traces = []
        
    def _build_transaction_graph(self) -> nx.DiGraph:
        """Build directed graph of fund flows"""
        G = nx.DiGraph()
        
        for tx in self.transactions:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            amount = float(tx.get('value', 0))
            
            if not from_addr or not to_addr:
                continue
                
            G.add_edge(from_addr, to_addr, weight=amount, tx=tx)
        
        return G
    
    def trace_fund_flow(self, source_address: str, max_depth: int = 10) -> Dict:
        """
        Trace funds from source address through the blockchain
        Returns: {paths, mixers_used, exchanges_used, total_flow}
        """
        source = source_address.lower()
        traces = {
            'source': source,
            'paths': [],
            'mixer_usage': [],
            'bridge_usage': [],
            'cex_deposits': [],
            'analysis': {
                'total_paths': 0,
                'max_depth': 0,
                'total_amount_traced': 0,
                'amount_lost_to_mixing': 0,
                'final_destinations': []
            }
        }
        
        if source not in self.graph:
            return traces
        
        # BFS to find all paths
        queue = deque([(source, [source], 0, float(self.graph.nodes[source].get('balance', 0)))])
        visited_paths = set()
        
        while queue:
            current, path, depth, amount = queue.popleft()
            
            if depth >= max_depth or len(path) > max_depth:
                traces['paths'].append({
                    'path': path,
                    'depth': len(path),
                    'final_amount': amount,
                    'terminated_at': path[-1]
                })
                continue
            
            # Track mixer usage
            if current in self.KNOWN_MIXERS.values():
                traces['mixer_usage'].append({
                    'mixer': current,
                    'found_at_depth': depth,
                    'amount_mixed': amount
                })
                traces['analysis']['amount_lost_to_mixing'] += amount * 0.02  # ~2% fees
            
            # Track bridge usage
            if current in self.KNOWN_BRIDGES.values():
                traces['bridge_usage'].append({
                    'bridge': current,
                    'found_at_depth': depth,
                    'amount_bridged': amount
                })
            
            # Track CEX deposits
            if current in self.KNOWN_CEXES.values():
                traces['cex_deposits'].append({
                    'exchange': current,
                    'found_at_depth': depth,
                    'amount_deposited': amount
                })
                traces['analysis']['final_destinations'].append({
                    'type': 'cex_deposit',
                    'address': current,
                    'amount': amount
                })
            
            # Continue tracing
            for successor in self.graph.successors(current):
                if successor not in path:  # Avoid cycles
                    edge_data = self.graph.get_edge_data(current, successor)
                    new_amount = amount - float(edge_data.get('weight', 0))
                    new_path = path + [successor]
                    
                    path_key = tuple(new_path)
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        queue.append((successor, new_path, depth + 1, new_amount))
        
        traces['analysis']['total_paths'] = len(traces['paths'])
        traces['analysis']['max_depth'] = max([len(p['path']) for p in traces['paths']], default=0)
        traces['analysis']['total_amount_traced'] = sum([p['final_amount'] for p in traces['paths']], default=0)
        
        return traces
    
    def detect_mixer_usage(self, transactions: List[Dict]) -> List[Dict]:
        """Detect when address interacted with mixing services"""
        mixer_interactions = []
        
        for tx in transactions:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            
            # Check if sending TO mixer
            if to_addr in self.KNOWN_MIXERS.values():
                mixer_interactions.append({
                    'type': 'mixer_deposit',
                    'address': to_addr,
                    'tx_hash': tx.get('hash'),
                    'amount': tx.get('value'),
                    'timestamp': tx.get('timeStamp'),
                    'risk': 'CRITICAL'
                })
            
            # Check if receiving FROM mixer (suspicious)
            if from_addr in self.KNOWN_MIXERS.values():
                mixer_interactions.append({
                    'type': 'mixer_withdrawal',
                    'address': from_addr,
                    'tx_hash': tx.get('hash'),
                    'amount': tx.get('value'),
                    'timestamp': tx.get('timeStamp'),
                    'risk': 'CRITICAL'
                })
        
        return mixer_interactions
    
    def detect_bridge_usage(self, transactions: List[Dict]) -> List[Dict]:
        """Detect cross-chain bridge usage"""
        bridge_activities = []
        
        for tx in transactions:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            
            if to_addr in self.KNOWN_BRIDGES.values():
                bridge_activities.append({
                    'type': 'bridge_transfer',
                    'bridge': to_addr,
                    'tx_hash': tx.get('hash'),
                    'amount': tx.get('value'),
                    'timestamp': tx.get('timeStamp'),
                    'risk': 'HIGH'
                })
            
            if from_addr in self.KNOWN_BRIDGES.values():
                bridge_activities.append({
                    'type': 'bridge_receipt',
                    'bridge': from_addr,
                    'tx_hash': tx.get('hash'),
                    'amount': tx.get('value'),
                    'timestamp': tx.get('timeStamp'),
                    'risk': 'MEDIUM'
                })
        
        return bridge_activities
    
    def analyze_atomic_swaps(self, transactions: List[Dict]) -> List[Dict]:
        """
        Detect atomic swap patterns
        Signs: Quick deposits to exchange, quick withdrawals on different chain
        """
        swaps = []
        
        # Group transactions by timestamp (within 5 minutes)
        time_groups = defaultdict(list)
        for tx in transactions:
            ts = int(tx.get('timeStamp', 0))
            bucket = ts // 300  # 5-minute buckets
            time_groups[bucket].append(tx)
        
        for bucket, txs in time_groups.items():
            if len(txs) >= 2:
                # Multiple txs within 5 minutes - possible atomic swap
                total_in = sum([float(tx.get('value', 0)) for tx in txs if tx.get('to') in self.KNOWN_CEXES.values()])
                total_out = sum([float(tx.get('value', 0)) for tx in txs if tx.get('from') in self.KNOWN_CEXES.values()])
                
                if total_in > 0 and total_out > 0:
                    swaps.append({
                        'type': 'atomic_swap_pattern',
                        'transactions': [tx.get('hash') for tx in txs],
                        'amount_in': total_in,
                        'amount_out': total_out,
                        'loss_percent': ((total_in - total_out) / total_in * 100) if total_in > 0 else 0,
                        'timestamp': bucket * 300,
                        'risk': 'HIGH'
                    })
        
        return swaps
    
    def get_fund_destination_summary(self, source_address: str) -> Dict:
        """
        Summary of where funds from source address ended up
        """
        traces = self.trace_fund_flow(source_address)
        
        summary = {
            'source': source_address,
            'destinations': {
                'mixers': len(traces['mixer_usage']),
                'bridges': len(traces['bridge_usage']),
                'exchanges': len(traces['cex_deposits']),
                'unknown': len(traces['paths']) - len(traces['cex_deposits'])
            },
            'total_traced': traces['analysis']['total_amount_traced'],
            'lost_to_fees': traces['analysis']['amount_lost_to_mixing'],
            'risk_assessment': self._assess_taint_risk(traces),
            'recommendations': self._generate_taint_recommendations(traces)
        }
        
        return summary
    
    def _assess_taint_risk(self, traces: Dict) -> Dict:
        """Assess risk based on taint analysis"""
        mixer_count = len(traces['mixer_usage'])
        bridge_count = len(traces['bridge_usage'])
        cex_count = len(traces['cex_deposits'])
        
        risk_score = 0
        risk_factors = []
        
        if mixer_count > 0:
            risk_score += 30
            risk_factors.append(f"Funds passed through {mixer_count} mixer(s)")
        
        if bridge_count > 0:
            risk_score += 15
            risk_factors.append(f"Cross-chain bridge activity detected ({bridge_count})")
        
        if cex_count > 0:
            risk_score -= 10  # Deposits to known exchanges reduce risk slightly
            risk_factors.append(f"Deposited to {cex_count} known exchange(s)")
        
        if traces['analysis']['max_depth'] > 5:
            risk_score += 15
            risk_factors.append("Deep chain of transfers (obfuscation attempt)")
        
        risk_score = min(100, max(0, risk_score))
        
        return {
            'risk_score': risk_score,
            'risk_level': 'CRITICAL' if risk_score >= 80 else 'HIGH' if risk_score >= 60 else 'MEDIUM' if risk_score >= 40 else 'LOW',
            'risk_factors': risk_factors
        }
    
    def _generate_taint_recommendations(self, traces: Dict) -> List[str]:
        """Generate recommendations based on taint analysis"""
        recommendations = []
        
        if len(traces['mixer_usage']) > 0:
            recommendations.append("⚠️  Funds passed through mixing service - identity obfuscation likely")
        
        if len(traces['bridge_usage']) > 0:
            recommendations.append("🌉 Cross-chain transfer detected - may indicate jurisdiction evasion")
        
        if len(traces['cex_deposits']) > 0:
            recommendations.append("✓ Funds deposited to known exchange - easier to trace further")
        
        if traces['analysis']['max_depth'] > 8:
            recommendations.append("🔄 Very long transfer chain - sophisticated evasion attempt")
        
        return recommendations
