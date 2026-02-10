from analyzer import analyze_live_chain
import networkx as nx
from db_models import SessionLocal, Case
from datetime import datetime

def verify_breadcrumbs_integration():
    print("[*] Starting Breadcrumbs Integration Verification")
    
    # 1. Create a Fake Case
    db = SessionLocal()
    case_id_str = f"TEST_BC_{int(datetime.now().timestamp())}"
    case = Case(case_id=case_id_str, case_name="Breadcrumbs Test")
    db.add(case)
    db.commit()
    print(f"[*] Created Case {case.id}")
    
    # 2. Run Analysis (This should trigger Breadcrumbs Mock)
    print("[*] Running Analysis on WANNACRY address...")
    summary, G, source = analyze_live_chain(
        address="13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94",
        chain="bitcoin",
        case_id=case.id
    )
    
    print(f"[*] Analysis Complete. Graph Size: {len(G.nodes)} nodes")
    
    # 3. Check for Enriched Data
    enriched_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "enriched"]
    print(f"[*] Enriched Nodes Found: {len(enriched_nodes)}")
    
    risk_factors = summary.get("risk_factors", [])
    breadcrumbs_factors = [f for f in risk_factors if "Breadcrumbs" in f]
    print(f"[*] Breadcrumbs Risk Factors: {breadcrumbs_factors}")
    
    if len(enriched_nodes) > 0 or len(breadcrumbs_factors) > 0:
        print("[+] SUCCESS: Breadcrumbs data integrated into Graph/Summary.")
    else:
        print("[!] FAILURE: No Breadcrumbs data found.")
        
    db.close()

if __name__ == "__main__":
    verify_breadcrumbs_integration()
