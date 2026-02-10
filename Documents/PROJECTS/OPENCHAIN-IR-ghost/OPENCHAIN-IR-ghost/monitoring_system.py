
import threading
import time
from datetime import datetime
from db_models import SessionLocal, Alert, Case, Address, Transaction
from eth_live import fetch_eth_address
from analyzer import analyze_live_eth, save_transactions

class MonitoringSystem:
    def __init__(self, interval=60):
        self.interval = interval
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("[*] Monitoring System Started")
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("[*] Monitoring System Stopped")
        
    def _monitor_loop(self):
        while self.running:
            try:
                self.check_addresses()
            except Exception as e:
                print(f"[!] Monitoring Error: {e}")
            
            time.sleep(self.interval)
            
    def check_addresses(self):
        db = SessionLocal()
        try:
            # Get all active cases
            cases = db.query(Case).filter(Case.status == 'active').all()
            
            for case in cases:
                for address_obj in case.addresses:
                    # Logic: Fetch latest txs, check if any are new (timestamp > last_checked)
                    # For simplicity, we can just fetch last 5 txs and check against DB hashes
                    # But fetch_eth_address gets all/page. 
                    # We can use a simplified fetch or check latest block.
                    # For V2, let's just fetch recent and deduplicate via save_transactions logic (which checks existing)
                    # But we need to know if we *saved* any new ones to trigger alert.
                    
                    self._check_single_address(db, case, address_obj)
                    
        finally:
            db.close()
            
    def _check_single_address(self, db, case, address_obj):
        # API Key (loaded from env in eth_live usually, or pass it)
        # Assuming eth_live handles env
        from eth_live import fetch_eth_address_with_counts
        import os
        API_KEY = os.getenv("ETHERSCAN_API_KEY")
        
        try:
            # Fetch recent txs (page 1)
            # We assume fetch_eth_address returns list of dicts
            txs = fetch_eth_address(address_obj.address, API_KEY, limit=20) 
            # Note: fetch_eth_address in eth_live doesn't have 'limit' param in my view? 
            # It has fetch_eth_address(address, api_key, chain_id, ...)
            # I should verify eth_live signature.
            # Viewed file says: fetch_eth_address(address, api_key, chain_id=1, ...)
            
            # Correction: fetch_eth_address fetches ALL by default loop.
            # I should implement a "fetch_latest" in eth_live or just use what I have but limit pages/recursion?
            # existing fetch_eth_address loops until end. That's expensive for polling.
            # I should modify eth_live or use requests directly here for lightweight polling.
            pass 
        except:
            pass
            
    # Redefining for implementation simplicity in this file
    def _fetch_recent_txs(self, address, api_key):
        import requests
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": "1",
            "module": "account",
            "action": "txlist",
            "address": address,
            "page": 1,
            "offset": 10, # Only last 10
            "sort": "desc",
            "apikey": api_key
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data['status'] == '1':
                return data['result']
        except:
            pass
        return []

    def _check_single_address(self, db, case, address_obj):
        import os
        API_KEY = os.getenv("ETHERSCAN_API_KEY")
        
        new_txs = self._fetch_recent_txs(address_obj.address, API_KEY)
        if not new_txs: return
        
        # Check against DB
        # Get latest known tx hash for this address
        # optimization: just check if hash exists
        
        alerts_triggered = 0
        
        for tx in new_txs:
            tx_hash = tx.get('hash')
            exists = db.query(Transaction).filter_by(tx_hash=tx_hash).first()
            
            if not exists:
                # NEW TRANSACTION FOUND
                # 1. Save it
                save_transactions(db, [tx], 1)
                
                # 2. Create Alert
                val = float(tx.get("value", 0)) / 1e18
                direction = "IN" if tx.get("to", "").lower() == address_obj.address.lower() else "OUT"
                
                alert = Alert(
                    case_id=case.id,
                    alert_type="new_transaction",
                    severity="medium", # logic could be better
                    address=address_obj.address,
                    description=f"New {direction} outcome: {val:.4f} ETH. Hash: {tx_hash[:10]}...",
                    related_tx_hash=tx_hash,
                    is_acknowledged=False,
                    created_at=datetime.utcnow()
                )
                db.add(alert)
                alerts_triggered += 1
                
        if alerts_triggered > 0:
            db.commit()
            print(f"[!] Generated {alerts_triggered} alerts for {address_obj.address}")

# Global instance
monitor = MonitoringSystem()
