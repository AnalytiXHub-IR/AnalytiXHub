import requests
import json
import os
import random
from datetime import datetime

class BreadcrumbsClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("BREADCRUMBS_API_KEY")
        self.base_url = "https://api.breadcrumbs.one"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        # Fallback mode if API fails or key is missing
        self.use_mock = False 

    def _request(self, method, endpoint, payload=None):
        if not self.api_key or self.use_mock:
            return None
            
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            else:
                response = requests.get(url, headers=self.headers, params=payload, timeout=10)
                
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"[Breadcrumbs] 403 Forbidden. Invalid Key? Switching to Mock Mode.")
                self.use_mock = True
                return None
            else:
                print(f"[Breadcrumbs] Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"[Breadcrumbs] Connection Error: {e}")
            return None

    def get_risk(self, address, chain="bitcoin"):
        """Get risk score and labels for an address."""
        # Try API
        endpoint = "/risk/address"
        payload = {"address": address, "chain": chain}
        data = self._request("POST", endpoint, payload)
        
        if data: return data
        
        # Fallback Mock Data
        print(f"[Breadcrumbs] Serving Mock Risk Data for {address[:8]}...")
        return self._generate_mock_risk(address)

    def get_transactions(self, address, chain="bitcoin", limit=10):
        """Get connected transactions/entities."""
        # Try API
        endpoint = "/smartexpand/transaction"
        payload = {"address": address, "chain": chain, "limit": limit}
        data = self._request("POST", endpoint, payload)
        
        if data: return data
        
        # Fallback Mock Data
        print(f"[Breadcrumbs] Serving Mock Transaction Data for {address[:8]}...")
        return self._generate_mock_transactions(address, limit)
        
    def _generate_mock_risk(self, address):
        """Generate realistic-looking risk data for demos."""
        # Deterministic based on address char to be consistent
        seed = sum(ord(c) for c in address)
        random.seed(seed)
        
        risk_score = random.randint(0, 100)
        labels = []
        
        if risk_score > 75:
            labels = ["Scam", "High Risk"]
        elif risk_score > 50:
            labels = ["Gambling", "Mixer"]
        elif risk_score > 25:
            labels = ["Exchange", "Service"]
        else:
            labels = ["Wallet", "User"]
            
        return {
            "address": address,
            "risk_score": risk_score / 100.0,
            "labels": labels,
            "monitor_status": "active"
        }

    def _generate_mock_transactions(self, address, limit):
        """Generate a star graph of transactions."""
        # Deterministic
        seed = sum(ord(c) for c in address)
        random.seed(seed)
        
        txs = []
        for _ in range(limit):
            is_incoming = random.choice([True, False])
            other_addr = f"{random.randint(1,9)}BC{random.randint(1000,9999)}MockAddress"
            
            tx = {
                "from": other_addr if is_incoming else address,
                "to": address if is_incoming else other_addr,
                "value": random.uniform(0.01, 2.5),
                "hash": f"mx{random.randint(100000, 999999)}",
                "timestamp": datetime.utcnow().timestamp(),
                "counterparty_label": random.choice(["Binance", "Unknown", "CoinJoin", "DarkMarket"])
            }
            txs.append(tx)
            
        return {"transactions": txs}
