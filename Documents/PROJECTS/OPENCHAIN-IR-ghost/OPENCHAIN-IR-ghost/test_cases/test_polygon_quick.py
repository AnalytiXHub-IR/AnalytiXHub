#!/usr/bin/env python3
"""
Quick test to verify Polygon chain works end-to-end
"""
import os
from dotenv import load_dotenv
from eth_live import fetch_eth_address_with_counts, SUPPORTED_CHAINS
from analyzer import analyze_live_eth

load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

print("=" * 70)
print("🧪 QUICK TEST: Polygon Chain Integration")
print("=" * 70)

# Test with a simple address
address = "0xe5277AA484C6d11601932bfFE553A55E37dC04Cf"
chain_name = "polygon"
chain_id = SUPPORTED_CHAINS[chain_name]

print(f"\n📍 Address: {address}")
print(f"🔗 Chain: {chain_name} (ID: {chain_id})")

try:
    # Step 1: Fetch transactions
    print("\n[1/3] Fetching transactions...", end=" ")
    txs, counts = fetch_eth_address_with_counts(
        address,
        API_KEY,
        chain_id=chain_id,
        include_internal=False,
        include_token_transfers=False
    )
    print(f"✅ Got {counts['normal']} transactions")
    
    # Step 2: Analyze
    print("[2/3] Analyzing...", end=" ")
    summary, G, source = analyze_live_eth(
        txs,
        address,
        chain_id=chain_id,
        chain_name=chain_name
    )
    print(f"✅ Analysis complete")
    
    # Step 3: Verify chain info
    print("[3/3] Verifying chain metadata...", end=" ")
    assert summary.get("chain_id") == chain_id, f"Chain ID mismatch: {summary.get('chain_id')} != {chain_id}"
    assert summary.get("chain_name") == chain_name, f"Chain name mismatch: {summary.get('chain_name')} != {chain_name}"
    print(f"✅ Chain metadata verified")
    
    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print(f"Chain ID in summary: {summary.get('chain_id')}")
    print(f"Chain Name in summary: {summary.get('chain_name')}")
    print(f"Total transactions: {summary.get('total_transactions')}")
    print(f"Risk score: {summary.get('risk_score')}")
    
    print("\n✅ TEST PASSED - Polygon integration works!")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
