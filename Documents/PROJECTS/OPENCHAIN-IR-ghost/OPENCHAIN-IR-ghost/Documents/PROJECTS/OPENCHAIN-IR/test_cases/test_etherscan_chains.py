#!/usr/bin/env python3
"""
Test Etherscan API across different chains
Etherscan supports: Ethereum, Sepolia, Holesky, Goerli
Polygon, Arbitrum, Optimism, Avalanche, Fantom, etc.
"""
import requests

key = 'TUWDXD7G5R3KE7K3UN1YD5F7RKKJIGXDEY'
addr = '0xbb5146F9Ab2e0105452AE3d52683FF15600e4150'

# Etherscan endpoints for different chains
endpoints = {
    'ethereum': 'https://api.etherscan.io/api',
    'polygon': 'https://api.polygonscan.com/api',
    'arbitrum': 'https://api.arbiscan.io/api',
    'optimism': 'https://api-optimistic.etherscan.io/api',
    'avalanche': 'https://api.snowtrace.io/api',
    'fantom': 'https://api.ftmscan.com/api',
    'bsc': 'https://api.bscscan.com/api',
}

print("Testing Etherscan API across chains...\n")

for chain, url in endpoints.items():
    try:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': addr,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'asc',
            'apikey': key
        }
        
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        status = data.get('status', '0')
        message = data.get('message', 'Unknown')
        result = data.get('result', [])
        
        if status == '1':
            print(f"✅ {chain.upper()}: {len(result)} transactions")
        elif 'No transactions' in message:
            print(f"⚠️  {chain.upper()}: No transactions for address")
        else:
            print(f"❌ {chain.upper()}: {message}")
            
    except Exception as e:
        print(f"❌ {chain.upper()}: {str(e)[:50]}")

print("\n✅ Found working chains - use their API endpoints with your key!")
