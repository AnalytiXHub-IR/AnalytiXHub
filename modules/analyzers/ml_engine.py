import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
import pandas as pd
from datetime import datetime
import time

class MLEngine:
    def __init__(self):
        self.iso_forest = IsolationForest(contamination=0.05, random_state=42)
        # Placeholder for pre-trained classifier
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_classifier_trained = False
        
    def detect_anomalies(self, transactions):
        """
        Detect anomalies in a list of transaction dictionaries using Isolation Forest.
        Enhanced Features: Value, Time Diff.
        """
        if not transactions or len(transactions) < 5:
            return []
            
        # Prepare Data
        data = []
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
        self.iso_forest.fit(X)
        predictions = self.iso_forest.predict(X) # -1 is anomaly
        scores = self.iso_forest.decision_function(X)
        
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                tx = ids[i]
                # Standardize output for template
                anom = {
                    'hash': tx.get('hash', tx.get('txid', 'Unknown')),
                    'amount': float(tx.get('value', 0)) / 10**18 if isinstance(tx.get('value'), str) and len(tx.get('value')) > 10 else float(tx.get('value', 0)), 
                    'timestamp': tx.get('timestamp', tx.get('timeStamp', 0)), # Keep original
                    'anomaly_score': round(float(1 - (scores[i] + 1) / 2), 4), # Normalized to 0-1 range
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

    def cluster_behavior(self, transactions):
        """
        DBSCAN Clustering: Group transactions by similarity to find hidden patterns
        (e.g., bot activity, scheduled transfers)
        """
        if len(transactions) < 10:
            return []
            
        # Feature Engineering for Clustering
        data = []
        for tx in transactions:
            try:
                val = float(tx.get('value', 0))
                # Minute of day as a feature for timing patterns
                ts_str = tx.get('timestamp', '')
                dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                min_of_day = dt.hour * 60 + dt.minute
                data.append([val, min_of_day])
            except:
                continue
        
        if len(data) < 10:
            return []
            
        X = np.array(data)
        dbscan = DBSCAN(eps=0.5, min_samples=3)
        clusters = dbscan.fit_predict(X)
        
        results = []
        unique_clusters = set(clusters)
        for cluster_id in unique_clusters:
            if cluster_id == -1: continue # Noise
            
            cluster_indices = np.where(clusters == cluster_id)[0]
            if len(cluster_indices) > 5:
                results.append({
                    'type': 'Behavioral Cluster',
                    'size': len(cluster_indices),
                    'cluster_id': int(cluster_id),
                    'description': f"Group of {len(cluster_indices)} transactions with highly similar value/timing signature."
                })
        
        return results

    def classify_address(self, address, txs):
        """
        Classify address type based on heuristics and ML
        """
        if not txs: return "Unknown"
        
        total_received = sum(float(tx.get('value', 0)) for tx in txs if tx.get('to', '').lower() == address.lower())
        total_sent = sum(float(tx.get('value', 0)) for tx in txs if tx.get('from', '').lower() == address.lower())
        tx_count = len(txs)
        unique_counterparties = len(set([tx.get('from') for tx in txs] + [tx.get('to') for tx in txs]))
        
        if tx_count > 500 and unique_counterparties > 100:
            return "Exchange / Hot Wallet"
            
        if any('Tornado' in str(tx) for tx in txs):
            return "High Risk (Mixer Interaction)"
            
        if total_sent > 0 and total_received > 0:
            ratio = total_sent / total_received
            if 0.98 <= ratio <= 1.02 and tx_count > 10:
                return "Potential Pass-through / Mixer"
        
        return "Individual / EOA"

    def detect_patterns(self, transactions, address):
        """
        Heuristic Pattern Detection augmented with ML analysis.
        """
        patterns = []
        
        # 1. Peeling Chain Detection
        out_txs = [tx for tx in transactions if tx.get('from', '').lower() == address.lower()]
        if len(out_txs) > 10:
            patterns.append({
                'type': 'High Frequency Outflow',
                'severity': 'Medium',
                'description': f"Detected {len(out_txs)} outflow transactions. Potential peeling chain or batch payment."
            })
        
        # 2. Add Clustering results to patterns
        clusters = self.cluster_behavior(transactions)
        for cluster in clusters:
            if cluster['size'] > 10:
                patterns.append({
                    'type': 'Automation / Bot Activity',
                    'severity': 'Medium',
                    'description': cluster['description']
                })

        return patterns

# Singleton
ml_engine = MLEngine()
