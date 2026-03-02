import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from modules.fetchers.multi_chain import AlchemyEVMFetcher

def debug_alchemy():
    chain = "galactica"
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    # Let's test galactica since the user mentioned it previously, or zksync
    chain2 = "zksync"
    
    out1 = AlchemyEVMFetcher._fetch_transfers(chain2, address, "from")
    print(f"Zksync Output: {out1}")
    
    # Try an extended network like worldchain
    out2 = AlchemyEVMFetcher._fetch_transfers("worldchain", address, "from")
    print(f"WorldChain Output: {out2}")
    
if __name__ == "__main__":
    debug_alchemy()
