#!/usr/bin/env python3
"""
INTERACTIVE TEST CASE
Test the cross-chain analysis with custom parameters
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
    print("🔍 OPENCHAIN IR - INTERACTIVE TEST CASE")
    print_separator()
    
    if not API_KEY:
        print("❌ Error: ETHERSCAN_API_KEY not found in .env")
        return False
    
    # Get parameters from user
    print("\n📝 Enter analysis parameters:")
    print("-" * 80)
    
    # 1. Address
    address = input("1️⃣  Blockchain Address (0x...): ").strip()
    if not address.startswith("0x") or len(address) != 42:
        print("❌ Invalid address format. Must be 0x followed by 40 hex characters")
        return False
    print(f"   ✅ Address: {address}")
    
    # 2. Chain Type
    print("\n2️⃣  Select Blockchain Chain:")
    print("   Available chains:")
    chain_names = sorted(SUPPORTED_CHAINS.keys())
    for i, chain in enumerate(chain_names, 1):
        chain_id = SUPPORTED_CHAINS[chain]
        print(f"      {i:2d}. {chain:15} (Chain ID: {chain_id})")
    
    while True:
        try:
            choice = int(input("\n   Enter chain number (1-15): "))
            if 1 <= choice <= len(chain_names):
                chain_name = chain_names[choice - 1]
                chain_id = SUPPORTED_CHAINS[chain_name]
                print(f"   ✅ Chain: {chain_name} (ID: {chain_id})")
                break
            else:
                print(f"   ❌ Please enter a number between 1 and {len(chain_names)}")
        except ValueError:
            print("   ❌ Invalid input. Please enter a number")
    
    # 3. Date From
    date_from = input("\n3️⃣  Date From (YYYY-MM-DD) or press Enter to skip: ").strip()
    if date_from and len(date_from) != 10:
        print("   ⚠️  Invalid date format. Will skip date filter")
        date_from = None
    elif date_from:
        print(f"   ✅ From: {date_from}")
    else:
        print("   ✅ From: All time")
        date_from = None
    
    # 4. Date To
    date_to = input("\n4️⃣  Date To (YYYY-MM-DD) or press Enter to skip: ").strip()
    if date_to and len(date_to) != 10:
        print("   ⚠️  Invalid date format. Will skip date filter")
        date_to = None
    elif date_to:
        print(f"   ✅ To: {date_to}")
    else:
        print("   ✅ To: Present")
        date_to = None
    
    # Confirm
    print_separator()
    print("🔄 STARTING ANALYSIS...")
    print_separator()
    
    try:
        # Step 1: Fetch transactions
        print(f"\n[1/3] Fetching transactions from {chain_name}...", end=" ")
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=chain_id,
            include_internal=False,
            include_token_transfers=False
        )
        print(f"✅\n       Found {counts['normal']} normal transactions")
        
        # Step 2: Analyze
        print(f"\n[2/3] Analyzing address...", end=" ")
        summary, G, source = analyze_live_eth(
            txs,
            address,
            start_date=date_from,
            end_date=date_to,
            chain_id=chain_id,
            chain_name=chain_name
        )
        print(f"✅")
        
        # Step 3: Display results
        print(f"\n[3/3] Formatting results...", end=" ")
        print(f"✅")
        
        # Results
        print_separator()
        print("📊 ANALYSIS RESULTS")
        print_separator()
        
        print(f"\n📍 Address: {address}")
        print(f"🔗 Chain: {chain_name.upper()} (ID: {chain_id})")
        print(f"📅 Period: {date_from or 'All time'} to {date_to or 'Present'}")
        
        print("\n💰 TRANSACTION SUMMARY:")
        print(f"   Total Transactions: {summary.get('total_transactions', 0)}")
        print(f"   Unique Senders: {summary.get('unique_senders', 0)}")
        print(f"   Unique Receivers: {summary.get('unique_receivers', 0)}")
        print(f"   Total Volume In: {summary.get('total_volume_in', 0):.4f}")
        print(f"   Total Volume Out: {summary.get('total_volume_out', 0):.4f}")
        print(f"   Net Flow: {summary.get('net_flow', 0):.4f}")
        
        print("\n📈 STATISTICS:")
        print(f"   Average Transaction: {summary.get('avg_transaction_value', 0):.4f}")
        print(f"   Median Transaction: {summary.get('median_transaction_value', 0):.4f}")
        print(f"   Max Transaction: {summary.get('max_transaction_value', 0):.4f}")
        
        print("\n🎯 RISK ASSESSMENT:")
        print(f"   Risk Score: {summary.get('risk_score', 0)}/100")
        print(f"   Confidence: {summary.get('confidence_score', 0)}%")
        
        risk_factors = summary.get('risk_factors', [])
        if risk_factors:
            print(f"   Risk Factors:")
            for factor in risk_factors:
                print(f"      • {factor}")
        else:
            print(f"   Risk Factors: None detected")
        
        print("\n🔍 DETECTED PATTERNS:")
        patterns = summary.get('patterns', {})
        pattern_count = 0
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, bool) and pattern_data:
                print(f"   ✅ {pattern_name.replace('_', ' ').title()}")
                pattern_count += 1
            elif isinstance(pattern_data, list) and pattern_data:
                print(f"   ✅ {pattern_name.replace('_', ' ').title()}: {len(pattern_data)} cases")
                pattern_count += 1
        
        if pattern_count == 0:
            print(f"   No suspicious patterns detected")
        
        print("\n👤 ENTITY INFORMATION:")
        entity_info = summary.get('entity_info', {})
        if entity_info:
            print(f"   Name: {entity_info.get('name', 'Unknown')}")
            print(f"   Type: {entity_info.get('type', 'Unknown')}")
            print(f"   Risk Level: {entity_info.get('risk', 'Unknown')}")
        else:
            print(f"   No known entity data")
        
        print("\n💼 TOP COUNTERPARTIES:")
        
        top_victims = summary.get('top_victims', [])
        if top_victims:
            print(f"   Top Senders (Victims):")
            for i, (addr, value) in enumerate(top_victims[:5], 1):
                print(f"      {i}. {addr[:10]}... : {value:.4f}")
        else:
            print(f"   Top Senders: None")
        
        top_suspects = summary.get('top_suspects', [])
        if top_suspects:
            print(f"   Top Receivers (Suspects):")
            for i, (addr, value) in enumerate(top_suspects[:5], 1):
                print(f"      {i}. {addr[:10]}... : {value:.4f}")
        else:
            print(f"   Top Receivers: None")
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
