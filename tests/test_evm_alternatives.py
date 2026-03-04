import requests
import json

def test_api(name, url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        data = res.json()
        
        # Etherscan/Blockscout V1 format (result list)
        if 'result' in data and isinstance(data['result'], list):
            print(f"{name}: OK - {len(data['result'])} txns (V1 API)")
        # Blockscout V2 format (items list)
        elif 'items' in data and isinstance(data['items'], list):
            print(f"{name}: OK - {len(data['items'])} txns (V2 API)")
        else:
            print(f"{name}: WARNING - Unknown format or error: {str(data)[:100]}")
    except Exception as e:
        print(f"{name}: ERROR - {str(e)[:100]}")

# Test Addresses (Known Active)
addr_bnb = '0x8894E0a0c962CB723c1976a4421c95949bE2D4E3'
addr_op = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045' # Vitalik
addr_base = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045' # Vitalik
addr_avax = '0x599E983De9bBBc9Cd6136Bae7B1C8DDe1D915f7B' # USDT AVAX
addr_ftm = '0xcb9bdfbeeb0f5854bace9ecaa89f921588d92661'
addr_zkevm = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045' # Vitalik

print("--- Testing Alternatives ---")
# 1. BNB -> BlockScout V1
test_api("BNB (BlockScout V1)", f"https://bsc.blockscout.com/api?module=account&action=txlist&address={addr_bnb}")
# 2. Optimism -> BlockScout V2
test_api("OP (BlockScout V2)", f"https://optimism.blockscout.com/api/v2/addresses/{addr_op}/transactions")
# 3. Base -> BlockScout V2
test_api("BASE (BlockScout V2)", f"https://base.blockscout.com/api/v2/addresses/{addr_base}/transactions")
# 4. Polygon zkEVM -> BlockScout V2
test_api("ZKEVM (BlockScout V2)", f"https://zkevm.blockscout.com/api/v2/addresses/{addr_zkevm}/transactions")
# 5. Avalanche -> Routescan V1
test_api("AVAX (Routescan V1)", f"https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api?module=account&action=txlist&address={addr_avax}")
# 6. Fantom -> Routescan V1
test_api("FTM (Routescan V1)", f"https://api.routescan.io/v2/network/mainnet/evm/250/etherscan/api?module=account&action=txlist&address={addr_ftm}")
