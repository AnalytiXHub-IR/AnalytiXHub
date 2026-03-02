import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from modules.fetchers.multi_chain import AlchemyEVMFetcher

# Test Alchemy with user payload directly against the backend
addr = "0xdd186D9E0c6A0EC8731E183a853EFB1eeC8438ec"

# test on a random alchemy chain
print("Testing zksync...")
txs, counts = AlchemyEVMFetcher.fetch_transactions("zksync", addr)
print(f"Results zksync: {counts['normal']}")

print("Testing worldchain...")
txs2, counts2 = AlchemyEVMFetcher.fetch_transactions("worldchain", addr)
print(f"Results worldchain: {counts2['normal']}")
