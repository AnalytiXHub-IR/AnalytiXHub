
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

# Setup logging manually
LOG_FILE = "backend_verification_log.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

try:
    from modules.fetchers.multi_chain import MultiChainFetcher, BlockCypherFetcher
    import modules.fetchers.multi_chain as mc_module
except Exception as e:
    log(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

def test_backend_integration():
    log(f"DEBUG: MultiChainFetcher file: {mc_module.__file__}")
    log(f"DEBUG: BlockCypher Token: {BlockCypherFetcher.API_TOKEN}")
    
    address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
    log(f"Testing Backend Integration for: {address}")
    
    try:
        # Call BlockCypherFetcher directly to isolate logic
        txs, counts = BlockCypherFetcher.fetch_transactions(address)
        
        log(f"[-] BlockCypherFetcher returned: {len(txs)} transactions")
        log(f"[-] Counts dict: {counts}")
        
        if len(txs) > 0:
            log(f"[-] First Tx Hash: {txs[0].get('hash')}")
            log(f"[-] Last Tx Hash: {txs[-1].get('hash')}")
            
        if len(txs) <= 10:
            log("[X] FAILURE: Still returning <= 10 transactions.")
        else:
            log("[OK] SUCCESS: Backend logic returns > 10 transactions.")
            
    except Exception as e:
        log(f"[X] ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend_integration()
