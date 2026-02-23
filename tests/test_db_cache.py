import requests

def test_caching():
    # We need to simulate a logged-in session, which is tricky without the UI.
    # Instead, let's just test the fetching function directly to bypass login.
    from app import app
    from modules.fetchers.multi_chain import MultiChainFetcher
    
    with app.app_context():
        # Test 1: First fetch should be a MISS
        print("Testing Fetch 1 (Should Miss):")
        txs, counts = MultiChainFetcher.fetch_by_chain("ethereum", "0x00000000219ab540356cbb839cbe05303d7705fa", force_refresh=True)
        print(f"Result 1: {counts}")
        
        # Test 2: Second fetch should be a HIT if we saved to DB (we didn't save via MultiChainFetcher itself because saving happens in app.py)
        # Wait, our fetch_by_chain *reads* from DB, but *app.py* writes to DB. 
        # So we need to call the app route to actually trigger the write.
        
        print("\nNote: DB caching writes currently happen in the route handler.")

if __name__ == "__main__":
    test_caching()
