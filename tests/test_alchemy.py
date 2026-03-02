import sys
import os
import json
from dotenv import load_dotenv

# Ensure modules package is accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from modules.fetchers.multi_chain import AlchemyEVMFetcher, ALCHEMY_API_KEY

def test_alchemy():
    print(f"Loaded API Key: {ALCHEMY_API_KEY}")
    
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Vitalik
    chain = "zksync" # Alchemy supported
    
    print(f"\n--- Testing fetch_transactions on {chain} ---")
    try:
        txs, counts = AlchemyEVMFetcher.fetch_transactions(chain, test_address)
        print(f"Success! Found {len(txs)} txs.")
        if txs:
            print("Sample TX:")
            print(json.dumps(txs[0], indent=2))
    except Exception as e:
        import traceback
        print(f"Crashed!")
        traceback.print_exc()

if __name__ == "__main__":
    test_alchemy()
