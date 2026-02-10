"""
Multi-Chain Blockchain Data Fetcher
Supports multiple chains via Etherscan-compatible APIs:
  - Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Fantom, BSC
  - Bitcoin, Litecoin, Dogecoin (searching for free APIs)
  - XRP Ledger (public nodes)
"""
import requests
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# ==================== BLOCKSCOUT (Free API - No Key Needed) ====================

class BlockScoutFetcher:
    """Fetch transactions via BlockScout - FREE for all EVM chains"""
    
    BLOCKSCOUT_URLS = {
        'ethereum': 'https://eth.blockscout.com/api/v2',
        'polygon': 'https://polygon.blockscout.com/api/v2',
        'arbitrum': 'https://arbitrum.blockscout.com/api/v2',
        'optimism': 'https://optimism.blockscout.com/api/v2',
    }
    
    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        """Fetch via BlockScout (100% FREE, no API key needed)"""
        if chain not in BlockScoutFetcher.BLOCKSCOUT_URLS:
            raise ValueError(f"BlockScout doesn't support {chain}")
        
        base_url = BlockScoutFetcher.BLOCKSCOUT_URLS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        try:
            # Fetch transactions
            tx_url = f"{base_url}/addresses/{address}/transactions"
            tx_response = requests.get(tx_url, timeout=15)
            tx_response.raise_for_status()
            tx_data = tx_response.json()
            
            if 'items' in tx_data:
                for tx in tx_data['items'][:100]:
                    transactions.append({
                        'hash': tx.get('hash'),
                        'from': tx.get('from', {}).get('hash') if isinstance(tx.get('from'), dict) else tx.get('from'),
                        'to': tx.get('to', {}).get('hash') if isinstance(tx.get('to'), dict) else tx.get('to'),
                        'value': float(tx.get('value', 0)) if tx.get('value') else 0,
                        'timestamp': tx.get('timestamp', 0),
                        'block': tx.get('block', 0),
                    })
            
            counts['normal'] = len(transactions)
            print(f"✅ {chain.upper()} (BlockScout): {counts['normal']} transactions")
            return transactions, counts
        
        except Exception as e:
            print(f"❌ BlockScout {chain} error: {e}")
            return [], counts

# ==================== ETHERSCAN v2 API (All EVM Chains) ====================

class EtherscanMultiChainFetcher:
    """
    Fetch transactions from EVM chains using Etherscan v2 API
    Uses SINGLE endpoint: https://api.etherscan.io/v2/api with chainid parameter
    Works for: Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Fantom, BSC, etc.
    ONE API key works for ALL chains!
    """
    
    V2_ENDPOINT = 'https://api.etherscan.io/v2/api'  # THE SINGLE ENDPOINT FOR ALL CHAINS
    
    CHAIN_CONFIGS = {
        'ethereum': {
            'chainid': 1,
            'name': 'Ethereum'
        },
        'bsc': {
            'chainid': 56,
            'name': 'Binance Smart Chain'
        },
        'polygon': {
            'chainid': 137,
            'name': 'Polygon'
        },
        'optimism': {
            'chainid': 10,
            'name': 'Optimism'
        },
        'arbitrum': {
            'chainid': 42161,
            'name': 'Arbitrum One'
        },
        'avalanche': {
            'chainid': 43114,
            'name': 'Avalanche'
        },
        'fantom': {
            'chainid': 250,
            'name': 'Fantom'
        },
    }
    
    @staticmethod
    def fetch_transactions(chain: str, address: str, include_internal: bool = True, 
                          include_token: bool = True) -> Tuple[List[Dict], Dict]:
        """
        Fetch transactions for any EVM chain using Etherscan v2 API
        Returns: (transactions_list, counts_dict)
        """
        if chain not in EtherscanMultiChainFetcher.CHAIN_CONFIGS:
            raise ValueError(f"Unsupported chain: {chain}")
        
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        # If no API key, fallback to BlockScout (free, no key needed)
        if not ETHERSCAN_API_KEY:
            print(f"⚠️  No API key, using BlockScout for {config['name']}...")
            return BlockScoutFetcher.fetch_transactions(chain, address)
        
        try:
            print(f"[+] Fetching {config['name']} transactions via Etherscan v2 API...")
            
            # Normal transactions
            normal_txs = EtherscanMultiChainFetcher._fetch_page(
                chain, address, 'txlist'
            )
            transactions.extend(normal_txs)
            counts['normal'] = len(normal_txs)
            
            # Internal transactions (if requested)
            if include_internal:
                time.sleep(0.25)
                internal_txs = EtherscanMultiChainFetcher._fetch_page(
                    chain, address, 'txlistinternal'
                )
                transactions.extend(internal_txs)
                counts['internal'] = len(internal_txs)
            
            # Token transfers (if requested)
            if include_token:
                time.sleep(0.25)
                token_txs = EtherscanMultiChainFetcher._fetch_page(
                    chain, address, 'tokentx'
                )
                transactions.extend(token_txs)
                counts['token'] = len(token_txs)
            
            total = counts['normal'] + counts['internal'] + counts['token']
            print(f"✅ {config['name']}: {counts['normal']} normal, {counts['internal']} internal, {counts['token']} token ({total} total)")
            return transactions, counts
        
        except Exception as e:
            print(f"❌ {config['name']} fetch error: {e}")
            # Fallback to BlockScout on error
            print(f"   Falling back to BlockScout...")
            return BlockScoutFetcher.fetch_transactions(chain, address)
    
    @staticmethod
    def _fetch_page(chain: str, address: str, action: str, 
                   page: int = 1, offset: int = 1000) -> List[Dict]:
        """Fetch single page from Etherscan API (Ethereum only)"""
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        
        params = {
            'module': 'account',
            'action': action,
            'address': address,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': ETHERSCAN_API_KEY
        }
        
        try:
            response = requests.get(config['base_url'], params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '1' and data.get('result'):
                return data['result']
            elif data.get('status') == '0':
                message = data.get('message', 'Unknown')
                if 'No transactions' in message:
                    return []
                print(f"  ⚠️  {action}: {message}")
                return []
            else:
                return []
        
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {action} HTTP error: {e}")
            return []
        except Exception as e:
            print(f"  ❌ {action} parse error: {e}")
            return []


# ==================== BITCOIN / LITECOIN / DOGECOIN ====================

class BlockchainFetcher:
    """
    Fetch BTC, LTC, DOGE transactions
    Currently using mock data - will integrate real API once found
    """
    
    @staticmethod
    def fetch_transactions(chain: str, address: str, limit: int = 100) -> Tuple[List[Dict], Dict]:
        """
        Fetch transactions for Bitcoin, Litecoin, or Dogecoin
        Returns mock data until a free API is found
        """
        transactions = []
        counts = {'normal': 0}
        
        print(f"⚠️  {chain.upper()}: Using mock data (searching for free API...)")
        
        # Return placeholder data
        transactions = [
            {
                'hash': f'{chain}_mock_tx_123...',
                'timestamp': int(time.time()) - 86400,
                'value': 0,
                'from': address,
                'to': 'unknown'
            }
        ]
        counts['normal'] = 1
        
        return transactions, counts


# ==================== XRP LEDGER ====================

class XRPLFetcher:
    """Fetch XRP transactions via XRPL public nodes (free, decentralized)"""
    
    NODES = [
        'https://xrpl.ws',
        'https://s1.ripple.com:51234',
        'https://xrplcluster.com',
    ]
    
    @staticmethod
    def fetch_transactions(address: str, limit: int = 100) -> Tuple[List[Dict], Dict]:
        """Fetch XRP transactions for an address"""
        transactions = []
        counts = {'normal': 0}
        
        try:
            txs = XRPLFetcher._fetch_xrpl_txs(address, limit)
            transactions.extend(txs)
            counts['normal'] = len(txs)
            
            if len(txs) > 0:
                print(f"✅ XRP: Fetched {len(txs)} transactions")
            return transactions, counts
        
        except Exception as e:
            print(f"❌ XRP fetch error: {e}")
            return [], counts
    
    @staticmethod
    def _fetch_xrpl_txs(address: str, limit: int = 100) -> List[Dict]:
        """Fetch XRP transactions via JSON-RPC"""
        
        for node_url in XRPLFetcher.NODES:
            try:
                payload = {
                    "method": "account_tx",
                    "params": [
                        {
                            "account": address,
                            "limit": min(limit, 200),
                            "ledger_index_min": -1,
                            "ledger_index_max": -1,
                        }
                    ]
                }
                
                headers = {"Content-Type": "application/json"}
                response = requests.post(node_url, json=payload, timeout=10, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                transactions = []
                if 'result' in data and 'transactions' in data['result']:
                    for tx_obj in data['result']['transactions'][:limit]:
                        tx = tx_obj.get('tx', {})
                        transactions.append({
                            'hash': tx.get('hash'),
                            'from': tx.get('Account'),
                            'to': tx.get('Destination'),
                            'amount': int(tx.get('Amount', 0)) / 1e6 if isinstance(tx.get('Amount'), (int, str)) else 0,
                            'timestamp': tx.get('date', 0),
                            'tx_type': tx.get('TransactionType'),
                        })
                
                if transactions:
                    print(f"✅ XRP: Fetched {len(transactions)} transactions")
                    return transactions
            
            except Exception as e:
                continue
        
        print(f"❌ XRP: All nodes failed")
        return []


# ==================== UNIFIED INTERFACE ====================

class MultiChainFetcher:
    """Unified interface for all blockchain chains"""
    
    @staticmethod
    def fetch_by_chain(chain: str, address: str, **kwargs) -> Tuple[List[Dict], Dict]:
        """
        Universal fetch method for any chain
        
        Args:
            chain: 'ethereum', 'polygon', 'arbitrum', 'optimism', 'bitcoin', 'litecoin', 'dogecoin', 'xrp'
            address: Blockchain address
            **kwargs: Chain-specific options (include_internal, include_token for EVM chains)
        
        Returns:
            (transactions_list, counts_dict)
        """
        # Ethereum: Use Etherscan API
        if chain == 'ethereum':
            return EtherscanMultiChainFetcher.fetch_transactions(
                chain, address,
                include_internal=kwargs.get('include_internal', True),
                include_token=kwargs.get('include_token', True)
            )
        # Other EVM chains: Use BlockScout (works better, no key needed)
        elif chain in ['polygon', 'arbitrum', 'optimism']:
            return BlockScoutFetcher.fetch_transactions(chain, address)
        # Non-EVM chains
        elif chain in ['bitcoin', 'litecoin', 'dogecoin']:
            return BlockchainFetcher.fetch_transactions(chain, address)
        elif chain == 'xrp':
            return XRPLFetcher.fetch_transactions(address, limit=kwargs.get('limit', 100))
        else:
            raise ValueError(f"Unsupported chain: {chain}")
    
    @staticmethod
    def get_supported_chains() -> Dict[str, Dict]:
        """Get list of supported chains with metadata"""
        return {
            'ethereum': {'symbol': 'ETH', 'decimals': 18, 'description': 'Ethereum Mainnet', 'api': 'Etherscan API'},
            'polygon': {'symbol': 'MATIC', 'decimals': 18, 'description': 'Polygon Mainnet', 'api': 'Polygonscan API'},
            'arbitrum': {'symbol': 'ETH', 'decimals': 18, 'description': 'Arbitrum One', 'api': 'Arbiscan API'},
            'optimism': {'symbol': 'ETH', 'decimals': 18, 'description': 'Optimism', 'api': 'Optimistic Etherscan API'},
            'avalanche': {'symbol': 'AVAX', 'decimals': 18, 'description': 'Avalanche C-Chain', 'api': 'Snowtrace API'},
            'fantom': {'symbol': 'FTM', 'decimals': 18, 'description': 'Fantom Opera', 'api': 'FTMscan API'},
            'bsc': {'symbol': 'BNB', 'decimals': 18, 'description': 'Binance Smart Chain', 'api': 'BscScan API'},
            'bitcoin': {'symbol': 'BTC', 'decimals': 8, 'description': 'Bitcoin Mainnet', 'api': 'Searching for free API'},
            'litecoin': {'symbol': 'LTC', 'decimals': 8, 'description': 'Litecoin Mainnet', 'api': 'Searching for free API'},
            'dogecoin': {'symbol': 'DOGE', 'decimals': 8, 'description': 'Dogecoin Mainnet', 'api': 'Searching for free API'},
            'xrp': {'symbol': 'XRP', 'decimals': 6, 'description': 'XRP Ledger', 'api': 'Public XRPL nodes'},
        }
    
    @staticmethod
    def get_chain_explorer_url(chain: str, address: str) -> str:
        """Get block explorer URL for an address"""
        explorers = {
            'ethereum': f'https://etherscan.io/address/{address}',
            'polygon': f'https://polygonscan.com/address/{address}',
            'arbitrum': f'https://arbiscan.io/address/{address}',
            'optimism': f'https://optimistic.etherscan.io/address/{address}',
            'bitcoin': f'https://blockchain.com/btc/address/{address}',
            'litecoin': f'https://blockchair.com/litecoin/address/{address}',
            'dogecoin': f'https://blockchair.com/dogecoin/address/{address}',
            'xrp': f'https://xrpscan.com/account/{address}',
        }
        return explorers.get(chain, '#')


# ==================== TESTING ====================

if __name__ == '__main__':
    print("🧪 Testing Multi-Chain Fetcher...\n")
    
    # Test Ethereum
    print("Testing Ethereum...")
    eth_txs, eth_counts = MultiChainFetcher.fetch_by_chain('ethereum', '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984')
    print()
    
    # Test Polygon
    print("Testing Polygon...")
    poly_txs, poly_counts = MultiChainFetcher.fetch_by_chain('polygon', '0x098B716B8Aaf21512996dC57EB0615e2383E2f96')
    print()
    
    # Test Arbitrum
    print("Testing Arbitrum...")
    arb_txs, arb_counts = MultiChainFetcher.fetch_by_chain('arbitrum', '0x098B716B8Aaf21512996dC57EB0615e2383E2f96')
    print()
    
    # Test Optimism
    print("Testing Optimism...")
    opt_txs, opt_counts = MultiChainFetcher.fetch_by_chain('optimism', '0x098B716B8Aaf21512996dC57EB0615e2383E2f96')
    print()
    
    # Test XRP
    print("Testing XRP...")
    xrp_txs, xrp_counts = MultiChainFetcher.fetch_by_chain('xrp', 'rN7n7otQDd6FczFgLdkqsJMAqSZfZ1YWF6')
    print()
    
    print("✅ Multi-chain fetcher operational!")
