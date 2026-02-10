
import requests
import time
from eth_live import fetch_eth_address_with_counts

class MultiChainFetcher:
    """
    Unified interface for fetching data from multiple blockchains.
    Supports: Ethereum (and EVM L2s), Solana, Bitcoin.
    """
    
    def __init__(self, api_keys=None):
        self.api_keys = api_keys or {}
        
    def fetch_transactions(self, chain, address):
        """
        Fetch transactions for a given chain and address.
        Returns: (tx_list, counts_summary)
        """
        chain = chain.lower()
        
        if chain == 'solana':
            return self._fetch_solana(address)
        elif chain == 'bitcoin':
            return self._fetch_bitcoin(address)
        elif chain == 'tron':
            return self._fetch_tron(address)
        elif chain in ['ethereum', 'polygon', 'bsc', 'arbitrum', 'optimism', 'base', 'avalanche', 'fantom', 'cronos', 'gnosis', 'celo', 'moonbeam', 'linea', 'blast', 'sepolia']:
            return self._fetch_evm(chain, address)
        else:
             # Try EVM fallback if it looks like an EVM address
             if address.startswith('0x') and len(address) == 42:
                 return self._fetch_evm(chain, address)
             raise ValueError(f"Unsupported chain: {chain}")

    def _fetch_evm(self, chain, address):
        """Delegate to existing eth_live module for EVM chains"""
        # Supported Chain IDs mapping
        chain_ids = {
            'ethereum': 1,
            'bsc': 56,
            'polygon': 137,
            'optimism': 10,
            'arbitrum': 42161,
            'base': 8453,
            'avalanche': 43114,
            'fantom': 250,
            'cronos': 25,
            'moonbeam': 1284,
            'gnosis': 100,
            'celo': 42220,
            'blast': 81457,
            'linea': 59144,
            'sepolia': 11155111,
        }
        
        chain_id = chain_ids.get(chain, 1)
        # Use specific key if available, else fallback to generic ETHERSCAN_API_KEY
        api_key = self.api_keys.get(f'{chain.upper()}_API_KEY') or self.api_keys.get('ETHERSCAN_API_KEY')
        
        if not api_key:
             print(f"Warning: No API Key for {chain}, using default or failing.")
        
        return fetch_eth_address_with_counts(address, api_key, chain_id=chain_id)

    def _fetch_solana(self, address):
        """Fetch Solana transactions via Solscan"""
        api_key = self.api_keys.get('SOLANA_API_KEY')
        base_url = "https://public-api.solscan.io" 
        headers = {'token': api_key} if api_key else {}
        
        try:
            url = f"{base_url}/account/transactions?account={address}&limit=50"
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code != 200:
                print(f"[Solana] Error: {r.status_code} - {r.text}")
                return [], {'normal': 0, 'internal': 0, 'token': 0}
                
            data = r.json()
            normalized_txs = []
            for tx in data:
                normalized_txs.append({
                    'hash': tx.get('txHash'),
                    'from': tx.get('src') or address,
                    'to': tx.get('dst'),
                    'value': tx.get('lamport', 0) / 1e9,
                    'timeStamp': tx.get('blockTime'),
                    'chain': 'solana'
                })
                
            return normalized_txs, {'normal': len(normalized_txs), 'internal': 0, 'token': 0}
            
        except Exception as e:
            print(f"[Solana] Fetch error: {e}")
            return [], {'normal': 0, 'internal': 0, 'token': 0}

    def _fetch_bitcoin(self, address):
        """Fetch Bitcoin transactions via Mempool.space (Free Tier)"""
        # Mempool.space API is free and robust
        base_url = "https://mempool.space/api"
        
        try:
            # Get TXs
            url = f"{base_url}/address/{address}/txs"
            r = requests.get(url, timeout=15)
            
            if r.status_code != 200:
                print(f"[Bitcoin] API Error: {r.status_code}")
                return [], {'normal': 0, 'internal': 0, 'token': 0}
                
            data = r.json() # List of tx objects
            normalized_txs = []
            
            for tx in data:
                total_val = 0
                # Calculate value sent TO the address
                for out in tx.get('vout', []):
                    if out.get('scriptpubkey_address') == address:
                        total_val += out.get('value', 0)
                
                # Determine sender (first input usually)
                sender = "coinbase"
                if tx.get('vin') and tx['vin'][0].get('prevout'):
                     sender = tx['vin'][0]['prevout'].get('scriptpubkey_address', 'unknown')
                
                normalized_txs.append({
                    'hash': tx.get('txid'),
                    'from': sender, 
                    'to': address,
                    'value': total_val / 1e8, # Satoshis to BTC
                    'timeStamp': tx.get('status', {}).get('block_time', time.time()),
                    'chain': 'bitcoin'
                })
            
            return normalized_txs, {'normal': len(normalized_txs), 'internal': 0, 'token': 0}
            
        except Exception as e:
             print(f"[Bitcoin] Fetch error: {e}")
             return [], {'normal': 0, 'internal': 0, 'token': 0}

    def _fetch_tron(self, address):
        """Fetch Tron transactions via TronScan"""
        api_key = self.api_keys.get('TRON_API_KEY')
        headers = {'TRON-PRO-API-KEY': api_key} if api_key else {}
        
        try:
            url = f"https://apilist.tronscan.org/api/transaction?sort=-timestamp&count=true&limit=50&start=0&address={address}"
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code != 200:
                print(f"[Tron] Error: {r.status_code}")
                return [], {'normal': 0}
                
            data = r.json()
            txs = data.get('data', [])
            normalized_txs = []
            
            for tx in txs:
                # TronScan returns amounts in Sun (1e6) but contract data varies
                amount = float(tx.get('amount', 0)) / 1e6 # TRX decimals
                
                normalized_txs.append({
                    'hash': tx.get('hash'),
                    'from': tx.get('ownerAddress'), 
                    'to': tx.get('toAddress'),
                    'value': amount,
                    'timeStamp': tx.get('timestamp', 0) / 1000, # ms to sec
                    'chain': 'tron'
                })
                
            return normalized_txs, {'normal': len(normalized_txs), 'internal': 0, 'token': 0}
            
        except Exception as e:
             print(f"[Tron] Fetch error: {e}")
             return [], {'normal': 0}
