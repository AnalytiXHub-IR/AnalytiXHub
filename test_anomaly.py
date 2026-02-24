import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from modules.analyzers.advanced_analysis import AnomalyDetector

def test_anomaly_logic():
    # Mock transactions: one clear outlier
    transactions = [
        {'value': 1.0, 'timeStamp': 1700000000, 'gasPrice': 20e9, 'isError': '0'},
        {'value': 1.1, 'timeStamp': 1700000100, 'gasPrice': 21e9, 'isError': '0'},
        {'value': 0.9, 'timeStamp': 1700000200, 'gasPrice': 19e9, 'isError': '0'},
        {'value': 1.05, 'timeStamp': 1700000300, 'gasPrice': 20.5e9, 'isError': '0'},
        {'value': 1.02, 'timeStamp': 1700000400, 'gasPrice': 20.2e9, 'isError': '0'},
        {'value': 1000.0, 'timeStamp': 1700000500, 'gasPrice': 100e9, 'isError': '0', 'hash': '0xANOMALY'}
    ]
    
    anomalies = AnomalyDetector.detect_anomalies(transactions)
    
    print(f"Number of anomalies: {len(anomalies)}")
    for anom in anomalies:
        print(f"Hash: {anom['hash']}")
        print(f"Score: {anom['anomaly_score']:.4f}")
        print(f"Is Suspicious: {anom['is_suspicious']}")
        print(f"Reasons: {anom['reasons']}")
        print("-" * 20)

if __name__ == "__main__":
    test_anomaly_logic()
