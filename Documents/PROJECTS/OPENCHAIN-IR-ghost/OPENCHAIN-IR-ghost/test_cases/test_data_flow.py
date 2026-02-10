#!/usr/bin/env python3
"""
Test data flow from API -> Analyzer -> Flask template
"""

import os
from dotenv import load_dotenv
from eth_live import fetch_eth_address_with_counts, SUPPORTED_CHAINS
from analyzer import analyze_live_eth

load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

def test_ethereum():
    """Test Ethereum data flow"""
    print("\n" + "="*80)
    print("TEST 1: ETHEREUM (Vitalik)")
    print("="*80)
    
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    chain_id = SUPPORTED_CHAINS["ethereum"]
    chain_name = "ethereum"
    
    try:
        # Step 1: Fetch
        print(f"\n[1/3] Fetching from {chain_name}...", end=" ")
        txs, counts = fetch_eth_address_with_counts(
            address, API_KEY, chain_id=chain_id
        )
        print(f"✅ Got {len(txs)} txs")
        
        # Step 2: Analyze
        print(f"[2/3] Analyzing...", end=" ")
        summary, G, source = analyze_live_eth(
            txs, address, 
            chain_id=chain_id,
            chain_name=chain_name
        )
        print(f"✅")
        
        # Step 3: Verify data structure
        print(f"[3/3] Verifying data structure...", end=" ")
        
        required_fields = [
            'total_transactions', 'total_volume_in', 'total_volume_out', 'net_flow',
            'unique_senders', 'unique_receivers', 'chain_id', 'chain_name',
            'risk_score', 'patterns', 'entity_info', 'top_victims', 'top_suspects'
        ]
        
        missing = [f for f in required_fields if f not in summary]
        if missing:
            print(f"❌ MISSING FIELDS: {missing}")
            return False
        
        print(f"✅")
        
        # Display summary
        print(f"\n📊 SUMMARY DATA:")
        print(f"  Address: {address}")
        print(f"  Chain: {summary['chain_name']} (ID: {summary['chain_id']})")
        print(f"  Total Txs: {summary['total_transactions']}")
        print(f"  Volume In: {summary['total_volume_in']}")
        print(f"  Volume Out: {summary['total_volume_out']}")
        print(f"  Net Flow: {summary['net_flow']}")
        print(f"  Risk Score: {summary['risk_score']}/100")
        print(f"  Unique Senders: {summary['unique_senders']}")
        print(f"  Unique Receivers: {summary['unique_receivers']}")
        print(f"  Entity: {summary['entity_info'].get('name', 'Unknown')}")
        print(f"  Top Victims: {len(summary['top_victims'])} found")
        print(f"  Top Suspects: {len(summary['top_suspects'])} found")
        
        print(f"\n✅ ETHEREUM TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_polygon():
    """Test Polygon data flow"""
    print("\n" + "="*80)
    print("TEST 2: POLYGON")
    print("="*80)
    
    address = "0xe5277AA484C6d11601932bfFE553A55E37dC04Cf"
    chain_id = SUPPORTED_CHAINS["polygon"]
    chain_name = "polygon"
    
    try:
        # Step 1: Fetch
        print(f"\n[1/3] Fetching from {chain_name}...", end=" ")
        txs, counts = fetch_eth_address_with_counts(
            address, API_KEY, chain_id=chain_id
        )
        print(f"✅ Got {len(txs)} txs")
        
        # Step 2: Analyze
        print(f"[2/3] Analyzing...", end=" ")
        summary, G, source = analyze_live_eth(
            txs, address, 
            chain_id=chain_id,
            chain_name=chain_name
        )
        print(f"✅")
        
        # Step 3: Verify data structure
        print(f"[3/3] Verifying data structure...", end=" ")
        
        required_fields = [
            'total_transactions', 'total_volume_in', 'total_volume_out', 'net_flow',
            'unique_senders', 'unique_receivers', 'chain_id', 'chain_name',
            'risk_score', 'patterns', 'entity_info', 'top_victims', 'top_suspects'
        ]
        
        missing = [f for f in required_fields if f not in summary]
        if missing:
            print(f"❌ MISSING FIELDS: {missing}")
            return False
        
        print(f"✅")
        
        # Display summary
        print(f"\n📊 SUMMARY DATA:")
        print(f"  Address: {address}")
        print(f"  Chain: {summary['chain_name']} (ID: {summary['chain_id']})")
        print(f"  Total Txs: {summary['total_transactions']}")
        print(f"  Volume In: {summary['total_volume_in']}")
        print(f"  Volume Out: {summary['total_volume_out']}")
        print(f"  Net Flow: {summary['net_flow']}")
        print(f"  Risk Score: {summary['risk_score']}/100")
        print(f"  Unique Senders: {summary['unique_senders']}")
        print(f"  Unique Receivers: {summary['unique_receivers']}")
        print(f"  Entity: {summary['entity_info'].get('name', 'Unknown')}")
        print(f"  Top Victims: {len(summary['top_victims'])} found")
        print(f"  Top Suspects: {len(summary['top_suspects'])} found")
        
        print(f"\n✅ POLYGON TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 TESTING DATA FLOW: API -> ANALYZER -> TEMPLATE")
    
    if not API_KEY:
        print("❌ ETHERSCAN_API_KEY not found in .env")
        exit(1)
    
    test1 = test_ethereum()
    test2 = test_polygon()
    
    print("\n" + "="*80)
    if test1 and test2:
        print("✅ ALL TESTS PASSED - DATA FLOW OK")
        print("="*80)
        exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*80)
        exit(1)
