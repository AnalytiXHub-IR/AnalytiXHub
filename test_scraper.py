
from modules.fetchers.dogechain_scraper import DogechainInfoScraper
import json

address = "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L"
try:
    txs, counts = DogechainInfoScraper.fetch_transactions(address)
    print(f"Scraper returned {len(txs)} transactions.")
    print(f"Counts: {counts}")
    if len(txs) > 0:
        print("Sample Tx:", json.dumps(txs[0], indent=2))
        print("Last Tx:", json.dumps(txs[-1], indent=2))
except Exception as e:
    print(f"Error: {e}")
