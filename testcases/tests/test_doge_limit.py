
from modules.fetchers.multi_chain import BlockCypherFetcher
import json

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
try:
    txs, counts = BlockCypherFetcher.fetch_transactions(address)
    print(f"Fetcher returned {len(txs)} transactions.")
    print(f"Counts: {counts}")
    if len(txs) > 0:
        print("Sample Tx:", json.dumps(txs[0], indent=2))
except Exception as e:
    print(f"Error: {e}")
