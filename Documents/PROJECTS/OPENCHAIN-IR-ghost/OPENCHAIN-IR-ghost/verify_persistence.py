import os
import sys
from datetime import datetime
from db_models import SessionLocal, Case, Transaction
from analyzer import analyze_live_chain
from graph_intelligence import GraphIntelligence

def verify_persistence():
    print("[*] Starting Persistence Verification")
    db = SessionLocal()
    
    # 1. Create a Test Case
    case_id_str = f"TEST_WANNACRY_{int(datetime.now().timestamp())}"
    print(f"[*] Creating Case: {case_id_str}")
    
    # Check if exists (unlikely with timestamp)
    case = Case(
        case_id=case_id_str,
        case_name="Wannacry Persistence Test",
        description="Automated Test",
        investigator="Automated Tester"
        # target_address is not in __init__ args if not defined in class body as Column? 
        # Wait, Case model does NOT have target_address column in the file I viewed!
        # Let's check db_models.py content I viewed earlier.
        # It has: items like case_id, case_name, description...
        # It DOES NOT have target_address column explicitly defined in the snippet I saw?
        # Let me re-read db_models.py snippet I stared at.
    )
    # Actually, looking at app.py: case.target_address = address
    # This implies the model has it.
    # Let's check db_models.py again. 
    # I see:
    # id, case_id, case_name, description, created_at, status, investigator, jurisdiction, case_type
    # relationships...
    # missing columns for UI compatibility: findings, timeline
    # AND NO target_address column in the Class definition!
    
    # Wait, app.py lines 144-146:
    # if case and address:
    #    case.target_address = address
    #    case.chain = chain
    #    db.commit()
    
    # If these columns don't exist in the model, SQLAlchemy will throw an error or it's dynamic?
    # SQLAlchemy models are essentially fixed.
    # Unless... I missed them in the view_file output?
    
    # Let's try to set them. If it fails, I'll know why app.py might be failing too (though app.py ran before).
    # Maybe they serve as ad-hoc attributes but won't persist if not columns.
    # But db.commit() would do nothing for them.
    
    # However, for this test, I need to pass case_id to analyze function.
    
    db.add(case)
    db.commit()
    print(f"[*] Case Created with DB ID: {case.id}")
    
    # 2. Run Analysis (should fetch and save)
    print("[*] Running Analysis...")
    try:
        summary, G, source = analyze_live_chain(
            address="13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94",
            chain="bitcoin",
            case_id=case.id # Pass the Integer ID
        )
    except Exception as e:
        print(f"[!] Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"[*] Analysis Complete. Graph Nodes (in memory): {len(G.nodes)}")
    
    # 3. Check Database Transactions
    # Check for txs LINKED to the case
    tx_count_linked = db.query(Transaction).filter_by(case_id=case.id).count()
    print(f"[*] DB BTC Transaction Count (Linked to Case {case.id}): {tx_count_linked}")
    
    if tx_count_linked == 0:
        print("[!] FAILURE: No transactions linked to case!")
    else:
        print("[+] SUCCESS: Transactions linked to case.")

    # 4. Check Graph Intelligence from DB
    print("[*] Building Graph via GraphIntelligence...")
    intel = GraphIntelligence()
    G_db = intel.build_case_graph(case.id)
    print(f"[*] Graph Nodes (from DB build): {len(G_db.nodes)}")
    
    if len(G_db.nodes) > 0:
         print("[+] SUCCESS: Graph built successfully from DB!")
    else:
         print("[!] FAILURE: Graph Empty.")
    
    db.close()

if __name__ == "__main__":
    verify_persistence()
