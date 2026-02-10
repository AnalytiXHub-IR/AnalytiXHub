import sys
import os
from datetime import datetime

# Setup path
sys.path.append(os.getcwd())

from db_models import SessionLocal, Case, Address, Transaction, ThreatIntel, init_db
from case_manager import CaseManager
from analyzer import save_transactions, identify_entity_type

def verify_persistence():
    print("[-] Verifying Persistence Layer...")
    
    # 1. Initialize DB
    # init_db() # Already initialized
    
    # 2. Case Manager Verification
    cm = CaseManager()
    case = cm.create_case("Persistence Test Case", "Testing DB integration", "Automated Tester")
    print(f"[+] Case Created: ID={case.case_id}, Name={case.case_name}")
    
    # Verify Case Retrieval
    case_db = cm.get_case(case.case_id)
    if case_db and case_db.case_name == "Persistence Test Case":
        print("[+] Case Retrieval Verified")
    else:
        print("[-] Case Retrieval Failed")
        
    # 3. Add Address
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Vitalik
    cm.add_address_to_case(case.case_id, addr, "suspect", "Known address")
    print(f"[+] Address {addr} added to case")
    
    # Verify Address Persistence
    case_db = cm.get_case(case.case_id)
    found = False
    for a in case_db.addresses:
        if a.address == addr:
            found = True
            print(f"[+] Address found in DB linked to case: Label={a.label}")
            break
    if not found:
        print("[-] Address NOT found in DB")
        
    # 4. Analyzer Connectivity & Threat Intel
    db = SessionLocal()
    try:
        # Check ThreatIntel
        ti = identify_entity_type(addr, [], db)
        print(f"[+] Entity Resolution: {ti['name']} ({ti['type']})")
        if ti['name'] == "Vitalik Buterin":
            print("[+] Threat Intelligence DB Lookup Successful")
        else:
            print("[-] Threat Intelligence Lookup Failed (Expected Vitalik)")
            
        # 5. Transaction Persistence
        dummy_txs = [
            {
                "hash": f"0xTEST_TX_{datetime.now().timestamp()}",
                "from": addr,
                "to": "0x0000000000000000000000000000000000000000",
                "value": "1000000000000000000", # 1 ETH
                "timeStamp": str(datetime.now().timestamp()),
                "blockNumber": "12345678",
                "gasUsed": "21000",
                "gasPrice": "50000000000",
                "input": "0x"
            }
        ]
        
        print("[+] Saving Dummy Transaction...")
        save_transactions(db, dummy_txs, 1)
        
        # Verify Transaction
        tx = db.query(Transaction).filter_by(tx_hash=dummy_txs[0]['hash']).first()
        if tx:
            print(f"[+] Transaction Persisted: {tx.tx_hash}, Amount={tx.amount}, Fee={tx.fee}")
        else:
            print("[-] Transaction Persistence Failed")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_persistence()
