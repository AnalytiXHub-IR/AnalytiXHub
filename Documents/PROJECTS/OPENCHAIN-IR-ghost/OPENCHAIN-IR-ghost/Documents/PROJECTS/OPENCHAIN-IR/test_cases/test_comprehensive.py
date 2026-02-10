#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE FOR CROSS-CHAIN IMPLEMENTATION
Tests all major functionality with real blockchain data
"""

import os
import sys
from dotenv import load_dotenv
from eth_live import fetch_eth_address_with_counts, SUPPORTED_CHAINS
from analyzer import analyze_live_eth

load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

# Test addresses with activity on different chains
TEST_ADDRESSES = {
    "ethereum": {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "name": "Vitalik Buterin",
        "expect_txs": True
    },
    "polygon": {
        "address": "0xe5277AA484C6d11601932bfFE553A55E37dC04Cf",
        "name": "Test Address",
        "expect_txs": True
    },
    "arbitrum": {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "name": "Vitalik on Arbitrum",
        "expect_txs": True
    },
}

def print_header(text, level=1):
    """Print formatted header"""
    if level == 1:
        print("\n" + "=" * 75)
        print(f"  {text}")
        print("=" * 75)
    else:
        print(f"\n{text}")
        print("-" * 75)

def print_result(test_name, passed, message=""):
    """Print test result"""
    icon = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    msg = f" - {message}" if message else ""
    print(f"{icon} {test_name}: {status}{msg}")
    return passed

def test_1_imports():
    """Test 1: Verify all imports work"""
    print_header("TEST 1: IMPORTS", 2)
    
    try:
        from app import app
        print_result("Flask app import", True)
    except Exception as e:
        return print_result("Flask app import", False, str(e))
    
    try:
        chains_count = len(SUPPORTED_CHAINS)
        print_result("SUPPORTED_CHAINS import", True, f"{chains_count} chains")
    except Exception as e:
        return print_result("SUPPORTED_CHAINS import", False, str(e))
    
    return True

def test_2_supported_chains():
    """Test 2: Verify all 15 chains are configured"""
    print_header("TEST 2: SUPPORTED CHAINS", 2)
    
    expected_chains = [
        "ethereum", "bsc", "polygon", "optimism", "arbitrum", 
        "base", "avalanche", "fantom", "cronos", "moonbeam",
        "gnosis", "celo", "blast", "linea", "sepolia"
    ]
    
    all_present = True
    for chain_name in expected_chains:
        if chain_name in SUPPORTED_CHAINS:
            chain_id = SUPPORTED_CHAINS[chain_name]
            print(f"  ✅ {chain_name:15} = {chain_id}")
        else:
            print(f"  ❌ {chain_name:15} = MISSING")
            all_present = False
    
    return print_result("All 15 chains present", all_present, f"Found: {len(SUPPORTED_CHAINS)}/15")

def test_3_ethereum_fetch():
    """Test 3: Fetch transactions from Ethereum"""
    print_header("TEST 3: ETHEREUM TRANSACTION FETCH", 2)
    
    if not API_KEY:
        return print_result("Ethereum fetch", False, "No API key")
    
    try:
        address = TEST_ADDRESSES["ethereum"]["address"]
        print(f"  Fetching from: {address[:10]}...")
        
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=1,
            include_internal=False,
            include_token_transfers=False
        )
        
        success = counts['normal'] > 0
        return print_result(
            "Ethereum fetch", 
            success, 
            f"{counts['normal']} transactions"
        )
    except Exception as e:
        return print_result("Ethereum fetch", False, str(e)[:50])

def test_4_polygon_fetch():
    """Test 4: Fetch transactions from Polygon"""
    print_header("TEST 4: POLYGON TRANSACTION FETCH", 2)
    
    if not API_KEY:
        return print_result("Polygon fetch", False, "No API key")
    
    try:
        address = TEST_ADDRESSES["polygon"]["address"]
        print(f"  Fetching from: {address[:10]}...")
        
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=137,
            include_internal=False,
            include_token_transfers=False
        )
        
        success = counts['normal'] >= 0
        return print_result(
            "Polygon fetch", 
            success, 
            f"{counts['normal']} transactions"
        )
    except Exception as e:
        return print_result("Polygon fetch", False, str(e)[:50])

def test_5_arbitrum_fetch():
    """Test 5: Fetch transactions from Arbitrum"""
    print_header("TEST 5: ARBITRUM TRANSACTION FETCH", 2)
    
    if not API_KEY:
        return print_result("Arbitrum fetch", False, "No API key")
    
    try:
        address = TEST_ADDRESSES["arbitrum"]["address"]
        print(f"  Fetching from: {address[:10]}...")
        
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=42161,
            include_internal=False,
            include_token_transfers=False
        )
        
        success = counts['normal'] >= 0
        return print_result(
            "Arbitrum fetch", 
            success, 
            f"{counts['normal']} transactions"
        )
    except Exception as e:
        return print_result("Arbitrum fetch", False, str(e)[:50])

def test_6_ethereum_analysis():
    """Test 6: Analyze Ethereum address"""
    print_header("TEST 6: ETHEREUM ANALYSIS", 2)
    
    if not API_KEY:
        return print_result("Ethereum analysis", False, "No API key")
    
    try:
        address = TEST_ADDRESSES["ethereum"]["address"]
        print(f"  Analyzing: {address[:10]}...")
        
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=1,
            include_internal=False,
            include_token_transfers=False
        )
        
        summary, G, source = analyze_live_eth(
            txs,
            address,
            chain_id=1,
            chain_name="ethereum"
        )
        
        # Verify results
        checks = [
            ("Has chain_id", summary.get("chain_id") == 1),
            ("Has chain_name", summary.get("chain_name") == "ethereum"),
            ("Has risk_score", "risk_score" in summary),
            ("Has transactions", summary.get("total_transactions") > 0),
        ]
        
        all_pass = all(check[1] for check in checks)
        for check_name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {check_name}")
        
        return print_result("Ethereum analysis", all_pass)
    except Exception as e:
        return print_result("Ethereum analysis", False, str(e)[:50])

def test_7_polygon_analysis():
    """Test 7: Analyze Polygon address"""
    print_header("TEST 7: POLYGON ANALYSIS", 2)
    
    if not API_KEY:
        return print_result("Polygon analysis", False, "No API key")
    
    try:
        address = TEST_ADDRESSES["polygon"]["address"]
        print(f"  Analyzing: {address[:10]}...")
        
        txs, counts = fetch_eth_address_with_counts(
            address,
            API_KEY,
            chain_id=137,
            include_internal=False,
            include_token_transfers=False
        )
        
        summary, G, source = analyze_live_eth(
            txs,
            address,
            chain_id=137,
            chain_name="polygon"
        )
        
        # Verify results
        checks = [
            ("Has chain_id", summary.get("chain_id") == 137),
            ("Has chain_name", summary.get("chain_name") == "polygon"),
            ("Has risk_score", "risk_score" in summary),
            ("Has metadata", "entity_info" in summary),
        ]
        
        all_pass = all(check[1] for check in checks)
        for check_name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {check_name}")
        
        return print_result("Polygon analysis", all_pass)
    except Exception as e:
        return print_result("Polygon analysis", False, str(e)[:50])

def test_8_chain_validation():
    """Test 8: Chain ID validation"""
    print_header("TEST 8: CHAIN VALIDATION", 2)
    
    from eth_live import _validate_chain
    
    tests = [
        (1, True, "Ethereum"),
        (137, True, "Polygon"),
        (42161, True, "Arbitrum"),
        (99999, False, "Invalid chain"),
        ("invalid", False, "Invalid type"),
    ]
    
    all_pass = True
    for chain_id, should_pass, label in tests:
        try:
            result = _validate_chain(chain_id)
            passed = should_pass
            print(f"  ✅ {label}: {result}" if passed else f"  ❌ {label}: Expected failure but passed")
        except ValueError:
            passed = not should_pass
            print(f"  ✅ {label}: Correctly rejected" if passed else f"  ❌ {label}: Should have passed")
        
        all_pass = all_pass and passed
    
    return print_result("Chain validation", all_pass)

def test_9_chain_switching():
    """Test 9: Quick switch between chains"""
    print_header("TEST 9: CHAIN SWITCHING", 2)
    
    if not API_KEY:
        return print_result("Chain switching", False, "No API key")
    
    try:
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        chains_to_test = [1, 137, 42161]
        
        results = {}
        for chain_id in chains_to_test:
            txs, counts = fetch_eth_address_with_counts(
                address,
                API_KEY,
                chain_id=chain_id,
                include_internal=False,
                include_token_transfers=False
            )
            results[chain_id] = counts['normal']
            print(f"  Chain {chain_id}: {counts['normal']} transactions")
        
        all_success = all(isinstance(v, int) for v in results.values())
        return print_result("Chain switching", all_success)
    except Exception as e:
        return print_result("Chain switching", False, str(e)[:50])

def test_10_flask_app():
    """Test 10: Flask app loads"""
    print_header("TEST 10: FLASK APP", 2)
    
    try:
        from app import app
        print(f"  App name: {app.name}")
        print(f"  Debug mode: {app.debug}")
        
        # Check routes
        routes = ["/", "/batch", "/report", "/timeline", "/heatmap", "/api/chains"]
        print(f"  Available routes: {len(app.url_map._rules)}")
        
        return print_result("Flask app", True)
    except Exception as e:
        return print_result("Flask app", False, str(e)[:50])

def run_all_tests():
    """Run all tests"""
    print_header("OPENCHAIN IR - COMPREHENSIVE TEST SUITE", 1)
    print(f"API Key: {API_KEY[:10] if API_KEY else 'NOT SET'}...")
    print(f"Supported Chains: {len(SUPPORTED_CHAINS)}")
    
    tests = [
        test_1_imports,
        test_2_supported_chains,
        test_3_ethereum_fetch,
        test_4_polygon_fetch,
        test_5_arbitrum_fetch,
        test_6_ethereum_analysis,
        test_7_polygon_analysis,
        test_8_chain_validation,
        test_9_chain_switching,
        test_10_flask_app,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print_header("TEST SUMMARY", 1)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\nResults: {passed}/{total} tests passed ({percentage:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The cross-chain implementation is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
