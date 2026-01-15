#!/usr/bin/env python3
"""
COMMAND-LINE TEST CASE
Usage: python test_cli.py <address> <chain> [date_from] [date_to]

Examples:
  python test_cli.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 ethereum
  python test_cli.py 0xe5277AA484C6d11601932bfFE553A55E37dC04Cf polygon
  python test_cli.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 ethereum 2025-11-01 2025-12-01
  python test_cli.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 arbitrum 2025-12-01 2025-12-24
"""

import os
import sys
from dotenv import load_dotenv
from eth_live import fetch_eth_address_with_counts, SUPPORTED_CHAINS
from analyzer import analyze_live_eth

load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

def print_separator():
    print("=" * 80)

def main():
    print_separator()
    print("🔍 OPENCHAIN IR - COMMAND-LINE TEST")
    print_separator()
    
    # Parse arguments
    if len(sys.argv) < 3:
        print("\n❌ Missing arguments!")
        print("\nUsage: python test_cli.py <address> <chain> [date_from] [date_to]")
        print("\nExample:")
        print("  python test_cli.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 ethereum")
        print("  python test_cli.py 0xe5277AA484C6d11601932bfFE553A55E37dC04Cf polygon 2025-12-01 2025-12-24")
        print("\nSupported Chains:")
        for i, chain in enumerate(sorted(SUPPORTED_CHAINS.keys()), 1):
            print(f"  {i:2d}. {chain}")
        return False
    
    address = sys.argv[1]
    chain_name = sys.argv[2].lower()
    date_from = sys.argv[3] if len(sys.argv) > 3 else None
    date_to = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Validate address
    if not address.startswith("0x") or len(address) != 42:
        print(f"\n❌ Invalid address: {address}")
        print("   Must be 0x followed by 40 hex characters")
        return False
    
    # Validate chain
    if chain_name not in SUPPORTED_CHAINS:
        print(f"\n❌ Invalid chain: {chain_name}")
        print(f"   Supported chains: {', '.join(sorted(SUPPORTED_CHAINS.keys()))}")
        return False
    
    chain_id = SUPPORTED_CHAINS[chain_name]
    
    # Validate API key
    if not API_KEY:
        print("❌ Error: ETHERSCAN_API_KEY not found in .env")
        return False
    
    # Display parameters
    print(f"\n📝 PARAMETERS:")
    print(f"   Address:  {address}")
    print(f"   Chain:    {chain_name.upper()} (ID: {chain_id})")
    print(f"   From:     {date_from or 'All time'}")
    print(f"   To:       {date_to or 'Present'}")
    
    print_separator()
    print("🔄 ANALYZING...")
    print_separator()
    
    try:
        # Step 1: Fetch
        print(f"\n[1/3] Fetching transactions...", end=" ", flush=True)
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=chain_id,
            include_internal=False,
            include_token_transfers=False
        )
        print(f"✅ ({counts['normal']} txs)")
        
        # Step 2: Analyze
        print(f"[2/3] Analyzing address...", end=" ", flush=True)
        summary, G, source = analyze_live_eth(
            txs,
            address,
            start_date=date_from,
            end_date=date_to,
            chain_id=chain_id,
            chain_name=chain_name
        )
        print(f"✅")
        
        # Step 3: Display
        print(f"[3/3] Formatting results...", end=" ", flush=True)
        print(f"✅")
        
        # Results
        print_separator()
        print("📊 RESULTS")
        print_separator()
        
        print(f"\n📍 Address: {address}")
        print(f"🔗 Chain: {chain_name.upper()} (ID: {chain_id})")
        
        print(f"\n💰 TRANSACTIONS:")
        print(f"   Total:            {summary.get('total_transactions', 0)}")
        print(f"   Unique Senders:   {summary.get('unique_senders', 0)}")
        print(f"   Unique Receivers: {summary.get('unique_receivers', 0)}")
        
        print(f"\n💵 VOLUME:")
        print(f"   Total In:   {summary.get('total_volume_in', 0):.6f}")
        print(f"   Total Out:  {summary.get('total_volume_out', 0):.6f}")
        print(f"   Net Flow:   {summary.get('net_flow', 0):.6f}")
        
        print(f"\n📈 STATISTICS:")
        print(f"   Average: {summary.get('avg_transaction_value', 0):.6f}")
        print(f"   Median:  {summary.get('median_transaction_value', 0):.6f}")
        print(f"   Max:     {summary.get('max_transaction_value', 0):.6f}")
        
        print(f"\n🎯 RISK:")
        print(f"   Score:      {summary.get('risk_score', 0)}/100")
        print(f"   Confidence: {summary.get('confidence_score', 0)}%")
        
        risk_factors = summary.get('risk_factors', [])
        if risk_factors:
            print(f"   Factors:")
            for factor in risk_factors:
                print(f"      • {factor}")
        
        print(f"\n🔍 PATTERNS DETECTED:")
        patterns = summary.get('patterns', {})
        detected = 0
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, bool) and pattern_data:
                print(f"   ✅ {pattern_name.replace('_', ' ').title()}")
                detected += 1
        
        if detected == 0:
            print(f"   No suspicious patterns")
        
        print(f"\n👤 ENTITY:")
        entity = summary.get('entity_info', {})
        if entity:
            print(f"   Name: {entity.get('name', 'Unknown')}")
            print(f"   Type: {entity.get('type', 'Unknown')}")
            print(f"   Risk: {entity.get('risk', 'Unknown')}")
        else:
            print(f"   Unknown entity")
        
        top_senders = summary.get('top_victims', [])
        if top_senders:
            print(f"\n📤 TOP SENDERS:")
            for i, (addr, value) in enumerate(top_senders[:3], 1):
                print(f"   {i}. {addr[:12]}... : {value:.6f}")
        
        top_receivers = summary.get('top_suspects', [])
        if top_receivers:
            print(f"\n📥 TOP RECEIVERS:")
            for i, (addr, value) in enumerate(top_receivers[:3], 1):
                print(f"   {i}. {addr[:12]}... : {value:.6f}")
        
        print_separator()
        print("✅ ANALYSIS COMPLETE")
        print_separator()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
