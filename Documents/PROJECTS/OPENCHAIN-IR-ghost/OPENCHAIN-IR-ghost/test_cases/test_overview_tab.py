#!/usr/bin/env python3
"""
Test that all overview tab data is present in Flask response
"""

import os
from dotenv import load_dotenv
from app import app

load_dotenv()

def test_overview_tab():
    """Test that all overview tab data is rendered"""
    print("\n" + "="*80)
    print("TESTING OVERVIEW TAB DATA RENDERING")
    print("="*80)
    
    client = app.test_client()
    
    print("\n[1/1] Submitting Ethereum analysis form...", end=" ")
    
    data = {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'chain': 'ethereum',
        'start_date': '',
        'end_date': '',
        'include_internal': 'off',
        'include_token_transfers': 'off'
    }
    
    response = client.post('/', data=data, follow_redirects=True)
    html_content = response.data.decode('utf-8', errors='ignore')
    
    # Check for required data fields
    required_fields = {
        'Chain ID': 'chain_id',
        'Chain Name': 'chain_name|ethereum|ethereum',
        'Total Transactions': 'total_transactions|Total Txs|Transactions',
        'Total Inflow': 'total_volume_in|Total Inflow',
        'Total Outflow': 'total_volume_out|Total Outflow',
        'Net Flow': 'net_flow|Net Flow',
        'Risk Score': 'risk_score|Risk Score',
        'Overview Tab': 'overview',
        'Metrics': 'Metric Summary',
    }
    
    missing = []
    found = []
    
    for field_name, patterns in required_fields.items():
        pattern_list = patterns.split('|')
        found_any = False
        for pattern in pattern_list:
            if pattern.lower() in html_content.lower():
                found_any = True
                break
        
        if found_any:
            found.append(field_name)
        else:
            missing.append(field_name)
    
    print(f"✅\n")
    
    print(f"\n📊 OVERVIEW TAB DATA CHECK:")
    print(f"\n✅ Found ({len(found)}):")
    for f in found:
        print(f"   • {f}")
    
    if missing:
        print(f"\n❌ Missing ({len(missing)}):")
        for m in missing:
            print(f"   • {m}")
        return False
    
    # Show sample values
    print(f"\n📈 RESPONSE INCLUDES:")
    if 'Vitalik' in html_content:
        print(f"   • Entity name recognized (Vitalik Buterin)")
    if '<button' in html_content and 'Report' in html_content:
        print(f"   • Report generation buttons present")
    if 'clusters' in html_content.lower() or 'clustering' in html_content.lower():
        print(f"   • Clustering results section present")
    
    print(f"\n✅ ALL REQUIRED OVERVIEW DATA IS RENDERING")
    return True

if __name__ == "__main__":
    print("🧪 OVERVIEW TAB DATA TEST")
    
    try:
        if test_overview_tab():
            print("\n" + "="*80)
            print("✅ OVERVIEW TAB TEST PASSED")
            print("   All required data is rendering in the web interface")
            print("="*80)
            exit(0)
        else:
            print("\n" + "="*80)
            print("❌ OVERVIEW TAB TEST FAILED")
            print("="*80)
            exit(1)
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
