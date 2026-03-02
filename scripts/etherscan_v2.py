"""
etherscan_v2.py
Utility for interacting with Etherscan V2 API across multiple chains.
"""
import requests

V2_ENDPOINT = "https://api.etherscan.io/v2/api"

CHAIN_IDS = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "optimism": 10,
    "arbitrum": 42161,
    "base": 8453,
    "avalanche": 43114,
    "fantom": 250,
    "cronos": 25,
    "moonbeam": 1284,
    "gnosis": 100,
    "celo": 42220,
    "blast": 81457,
    "linea": 59144,
    "sepolia": 11155111,
}

class EtherscanV2:
    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = V2_ENDPOINT

    def get_balance(self, address, chain_id):
        params = {
            "chainid": chain_id,
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key
        }
        response = requests.get(self.endpoint, params=params)
        data = response.json()
        if data.get('status') == '1':
            return int(data['result']) / 10**18
        else:
            return f"Error: {data.get('message', 'Unknown error')}"

    def get_balance_by_name(self, address, chain_name):
        chain_id = CHAIN_IDS.get(chain_name.lower())
        if not chain_id:
            raise ValueError(f"Unsupported chain name: {chain_name}")
        return self.get_balance(address, chain_id)
