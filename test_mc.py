import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from modules.fetchers.multi_chain import MultiChainFetcher

def test():
    # An address the user tested earlier
    address = "0x251D3113D319E2F3644fC222360a05688D5dC013" # Base address from logs
    address2 = "0x0baa722AefA911A4F7e7657198bCDB9EFc06Bf38" # zksync address from logs
    
    print("Testing zksync via MultiChainFetcher...")
    txs, counts = MultiChainFetcher.fetch_by_chain("zksync", address2, force_refresh=True)
    print(f"Zksync returns {len(txs)} txs")
    
    # Try another address on an extended chain
    print("Testing worldchain...")
    txs2, counts2 = MultiChainFetcher.fetch_by_chain("worldchain", "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", force_refresh=True)
    print(f"Worldchain returns {len(txs2)} txs")

if __name__ == "__main__":
    test()
