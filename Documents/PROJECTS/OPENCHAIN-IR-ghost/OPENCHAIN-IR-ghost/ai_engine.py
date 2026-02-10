
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from db_models import SessionLocal, Address, Transaction, AnomalyDetection

class AIEngine:
    def __init__(self, model_path="models/"):
        self.model_path = model_path
        self.scaler = StandardScaler()
        self.anomaly_model = None
        self.classifier_model = None
        
        if not os.path.exists(model_path):
            os.makedirs(model_path)
            
        self._load_or_train_models()
        
    def _load_or_train_models(self):
        """Load existing models or train new ones with seed data"""
        try:
            with open(os.path.join(self.model_path, "anomaly_model.pkl"), "rb") as f:
                self.anomaly_model = pickle.load(f)
            with open(os.path.join(self.model_path, "classifier_model.pkl"), "rb") as f:
                self.classifier_model = pickle.load(f)
            print("[+] AI Models loaded successfully.")
        except FileNotFoundError:
            print("[*] Models not found. Training new models...")
            self.train_models()
            
    def train_models(self):
        """Train models on seeded/synthetic data"""
        # 1. Anomaly Detection (Isolation Forest)
        # Features: [avg_amount, tx_frequency, time_variance, unique_counterparties]
        # Generate synthetic normal data
        X_normal = np.random.normal(loc=[1.5, 10, 5000, 5], scale=[0.5, 2, 1000, 2], size=(100, 4))
        # Generate synthetic anomalies (spikes, high frequency)
        X_anom = np.random.normal(loc=[10.0, 50, 200, 20], scale=[2.0, 10, 50, 5], size=(10, 4))
        X_train = np.vstack([X_normal, X_anom])
        
        self.anomaly_model = IsolationForest(contamination=0.1, random_state=42)
        self.anomaly_model.fit(X_train)
        
        # 2. Wallet Classifier (Random Forest)
        # Classes: 0=User, 1=Exchange, 2=Mixer, 3=Scammer
        # Features: [in_out_ratio, avg_gas, unique_peers, tx_count]
        X_clf = np.array([
            [1.0, 21000, 5, 50],   # User
            [1.0, 21000, 1000, 5000], # Exchange
            [0.1, 50000, 50, 100], # Mixer (high fan-out?)
            [5.0, 30000, 2, 10]    # Scammer (mostly in, few out)
        ])
        y_clf = np.array([0, 1, 2, 3])
        # Expand dataset slightly
        X_clf_train = np.repeat(X_clf, 10, axis=0) # Simple repetition for seed
        y_clf_train = np.repeat(y_clf, 10)
        
        self.classifier_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.classifier_model.fit(X_clf_train, y_clf_train)
        
        # Save
        with open(os.path.join(self.model_path, "anomaly_model.pkl"), "wb") as f:
            pickle.dump(self.anomaly_model, f)
        with open(os.path.join(self.model_path, "classifier_model.pkl"), "wb") as f:
            pickle.dump(self.classifier_model, f)
            
        print("[+] AI Models trained and saved.")

    def analyze_address_behavior(self, address_str):
        """Full AI analysis of an address"""
        db = SessionLocal()
        try:
            # 1. Aggregate Features from DB
            txs = db.query(Transaction).filter(
                (Transaction.from_address == address_str) | (Transaction.to_address == address_str)
            ).all()
            
            if not txs:
                return {"risk_score": 0, "type": "Unknown", "anomalies": []}
            
            # Feature Extraction
            amounts = [t.amount for t in txs]
            timestamps = [t.timestamp.timestamp() for t in txs]
            peers = set([t.from_address for t in txs] + [t.to_address for t in txs])
            
            avg_amt = np.mean(amounts) if amounts else 0
            tx_count = len(txs)
            unique_peers = len(peers)
            
            # Time variance (inter-arrival time)
            if len(timestamps) > 1:
                timestamps.sort()
                deltas = np.diff(timestamps)
                time_var = np.var(deltas)
            else:
                time_var = 0
                
            # Ratio In/Out
            sent = sum(1 for t in txs if t.from_address == address_str)
            received = sum(1 for t in txs if t.to_address == address_str)
            ratio = sent / received if received > 0 else sent
            
            # 2. Run Anomaly Detection
            # Feature vector: [avg_amount, tx_count, time_var, unique_peers]
            features_anom = np.array([[avg_amt, tx_count, time_var, unique_peers]])
            is_anomaly = self.anomaly_model.predict(features_anom)[0] == -1
            anomaly_score = self.anomaly_model.score_samples(features_anom)[0] # negative, lower is more anomalous
            
            # 3. Run Classification
            # Features: [in_out_ratio, avg_gas(mocked), unique_peers, tx_count]
            features_clf = np.array([[ratio, 21000, unique_peers, tx_count]])
            class_idx = self.classifier_model.predict(features_clf)[0]
            class_labels = {0: "User", 1: "Exchange", 2: "Mixer", 3: "Suspect/Scammer"}
            predicted_type = class_labels.get(class_idx, "Unknown")
            
            # 4. Calculate Risk Score (0-100)
            base_risk = 0
            if is_anomaly: base_risk += 40
            if predicted_type in ["Mixer", "Suspect/Scammer"]: base_risk += 50
            if predicted_type == "Exchange": base_risk = 10 # Low risk usually
            
            # Normalize anomaly score (-0.5 to 0.5 roughly) -> 0-20 points
            base_risk += abs(min(anomaly_score, 0)) * 20
            
            risk_score = min(max(base_risk, 0), 100)
            
            # Save Anomaly Record if high
            if is_anomaly:
                self._save_anomaly(db, address_str, anomaly_score, risk_score)
            
            return {
                "risk_score": round(risk_score, 2),
                "predicted_type": predicted_type,
                "is_anomaly": bool(is_anomaly),
                "confidence": 0.85 # Mock confidence
            }
            
        finally:
            db.close()
            
    def _save_anomaly(self, db, address, score, risk):
        # Check if already exists recently?
        exists = db.query(AnomalyDetection).filter_by(address=address).first()
        if not exists:
            anom = AnomalyDetection(
                address=address,
                chain="ethereum",
                anomaly_type="Behavioral Outlier",
                anomaly_score=float(score),
                confidence=0.85,
                detected_at=datetime.utcnow(),
                extra_metadata={"risk_score": risk}
            )
            db.add(anom)
            db.commit()

# Global Instance
ai_engine = AIEngine()
