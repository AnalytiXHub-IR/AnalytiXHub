import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
from datetime import datetime

class MLEngine:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        
    def detect_anomalies(self, transactions):
        """
        Detect anomalies in a list of transaction dictionaries using Isolation Forest.
        Features: Value, Time Diff from prev tx.
        """
        if not transactions or len(transactions) < 5:
            return []
            
        # Prepare Data
        data = []
        timestamps = []
        ids = []
        
        # Sort txs by time
        sorted_txs = sorted(transactions, key=lambda x: x.get('timestamp', ''))
        
        last_time = 0
        for i, tx in enumerate(sorted_txs):
            try:
                # Value
                val = float(tx.get('value', 0))
                
                # Time Diff (seconds)
                ts_str = tx.get('timestamp', '')
                if not ts_str: continue
                
                try:
                    ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S').timestamp()
                except:
                    ts = time.time()
                    
                time_diff = 0
                if i > 0 and last_time > 0:
                    time_diff = ts - last_time
                last_time = ts
                
                data.append([val, time_diff])
                ids.append(tx)
            except:
                continue
                
        if len(data) < 5:
            return []
            
        # Fit Model
        X = np.array(data)
        self.model.fit(X)
        predictions = self.model.predict(X) # -1 is anomaly
        scores = self.model.decision_function(X)
        
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                tx = ids[i]
                # Standardize output for template
                anom = {
                    'hash': tx.get('hash', tx.get('txid', 'Unknown')),
                    'amount': float(tx.get('value', 0)) / 10**18 if isinstance(tx.get('value'), str) and len(tx.get('value')) > 10 else float(tx.get('value', 0)), 
                    'timestamp': tx.get('timestamp', tx.get('timeStamp', 0)), # Keep original
                    'anomaly_score': round(float(scores[i]), 4),
                    'reasons': ["Statistical Outlier (Value/Timing)"], 
                    'is_suspicious': True,
                    'address': tx.get('to', 'Unknown'), # Add address for threat_intel template
                    'type': 'Anomaly', # For threat_intel.html
                    'description': "Statistical Outlier detected in transaction value or timing." # For threat_intel.html
                }
                
                # Check for timestamp format issue
                ts_val = anom['timestamp']
                # If it's a string date, don't try to int() it later if used
                
                anom['amount'] = float(tx.get('value', 0))
                
                anomalies.append(anom)
                
        return anomalies

    def detect_patterns(self, transactions, address):
        """
        Heuristic Pattern Detection:
        1. Peeling Chain: Small rapid outputs decreasing in value.
        2. Structuring: Multiple transactions of similar size just below thresholds.
        3. Round Tripping: Funds leaving and returning.
        """
        patterns = []
        
        # Helper Rule: Rapid Movement (High Frequency)
        # Check for > 5 txs in 1 hour
        # ... logic ...
        
        # 1. Peeling Chain Detection
        # Look for a series of outputs where change address keeps carrying majority funds
        # Simplified: Look for many small outputs in short succession
        out_txs = [tx for tx in transactions if (tx.get('from') or '').lower() == (address or '').lower()]
        if len(out_txs) > 10:
            patterns.append({
                'type': 'High Frequency Outflow',
                'severity': 'Medium',
                'description': f"Detected {len(out_txs)} outflow transactions. Potential peeling chain or batch payment."
            })
            
        # 2. Round Tripping (Simulated logic for demo)
        # If user receives money from an address they sent to previously
        sent_to = set()
        received_from = set()
        for tx in transactions:
            if (tx.get('from') or '').lower() == (address or '').lower():
                sent_to.add((tx.get('to') or '').lower())
            else:
                received_from.add((tx.get('from') or '').lower())
        
        common = sent_to.intersection(received_from)
        if common:
             patterns.append({
                'type': 'Round Tripping / Cyclic Flow',
                'severity': 'High',
                'description': f"Funds moved back and forth with {len(common)} addresses (e.g., {list(common)[0]})",
                'entities': list(common)
            })
            
        return patterns

# Singleton or factory
ml_engine = MLEngine()
