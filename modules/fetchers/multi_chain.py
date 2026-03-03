"""
Multi-Chain Blockchain Data Fetcher
Supports multiple chains via official and public APIs:
  - EVM Chains: Ethereum, Polygon, Arbitrum, Optimism, BSC (Etherscan v2 / BlockScout)
  - Bitcoin: Mempool.space (Free)
  - Solana: Solscan Public API v2 (Official)
  - Tron: TronGrid / TronScan (Official)
  - XRP: XRPL Public Nodes
"""
import requests
import time
import random
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
SOLANA_API_KEY = os.getenv('SOLANA_API_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3NzA3MTg3MzU5ODAsImVtYWlsIjoia29sbHVydXNhaWFiaGlyYW01MTNAZ21haWwuY29tIiwiYWN0aW9uIjoidG9rZW4tYXBpIiwiYXBpVmVyc2lvbiI6InYyIiwiaWF0IjoxNzcwNzE4NzM1fQ.SGdL7FJRYiMhC5YnSky-6UXCa4NLOgkoWSvhD2AvRDg")
HELIUS_API_KEY = os.getenv('HELIUS_API_KEY', "a44ade62-a70f-4b75-8054-3e8388f70058")
TRON_API_KEY = os.getenv('TRON_API_KEY', "72ac1d93-4497-4664-a844-f730b2b5e606")
MORALIS_API_KEY = os.getenv('MORALIS_API_KEY', '')
COVALENT_API_KEY = os.getenv('COVALENT_API_KEY', '')

# Global Checksum Helper
try:
    from web3 import Web3
    w3 = Web3()
    def safe_checksum(addr):
        try:
            if addr and isinstance(addr, str) and addr != 'Unknown' and addr.startswith('0x'):
                return w3.to_checksum_address(addr.lower())
        except:
            pass
        return addr
except ImportError:
    def safe_checksum(addr): return addr

# ==================== BLOCKSCOUT (Free EVM API) ====================

class BlockScoutFetcher:
    """Fetch transactions via BlockScout - FREE for all EVM chains"""
    
    BLOCKSCOUT_URLS = {
        'ethereum': 'https://eth.blockscout.com/api/v2',
        'polygon': 'https://polygon.blockscout.com/api/v2',
        'arbitrum': 'https://arbitrum.blockscout.com/api/v2',
        'optimism': 'https://optimism.blockscout.com/api/v2',
        'base': 'https://base.blockscout.com/api/v2',
        'base_sepolia': 'https://base-sepolia.blockscout.com/api/v2',
        'gnosis': 'https://gnosis.blockscout.com/api/v2',
        'celo': 'https://explorer.celo.org/mainnet/api/v2',
        'blast': 'https://blast.blockscout.com/api/v2',
        'linea': 'https://explorer.linea.build/api/v2',
        'moonbeam': 'https://moonbeam.blockscout.com/api/v2',
        'cronos': 'https://cronos.blockscout.com/api/v2',
        'polygon_zkevm': 'https://zkevm.blockscout.com/api/v2',
        'mantle': 'https://explorer.mantle.xyz/api/v2',
        'bob': 'https://explorer.gobob.xyz/api/v2',
        'botanix': 'https://blockscout.botanixlabs.dev/api/v2',
        'galactica': 'https://explorer.galactica.com/api/v2',
        'opbnb': 'https://opbnb.blockscout.com/api/v2',
        'sei': 'https://seitrace.com/api/v2',
    }
    
    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        """Fetch via BlockScout (100% FREE, no API key needed)"""
        chain = chain.lower()
        if chain not in BlockScoutFetcher.BLOCKSCOUT_URLS:
            return [], {'normal': 0, 'internal': 0, 'token': 0}
        
        base_url = BlockScoutFetcher.BLOCKSCOUT_URLS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        try:
            tx_url = f"{base_url}/addresses/{address}/transactions"
            params = {}
            
            while True:
                tx_response = requests.get(tx_url, params=params, timeout=15)
                
                if tx_response.status_code == 200:
                    tx_data = tx_response.json()
                    if 'items' in tx_data:
                        for tx in tx_data['items']: # Process all returned items
                            transactions.append({
                            'hash': tx.get('hash'),
                            'from': safe_checksum(tx.get('from', {}).get('hash') if isinstance(tx.get('from'), dict) else tx.get('from')),
                            'to': safe_checksum(tx.get('to', {}).get('hash') if isinstance(tx.get('to'), dict) else tx.get('to', 'Unknown')),
                            'value': float(tx.get('value', 0)) / 1e18 if tx.get('value') else 0.0,
                            'timestamp': tx.get('timestamp') or datetime.now().isoformat(),
                            'block': tx.get('block', 0),
                            'chain': chain,
                            'type': 'transfer'
                        })    
                    # Pagination logic
                    next_page = tx_data.get('next_page_params')
                    # Set a hard limit at 10000 to prevent ultra-massive wallets hanging the server indefinitely
                    if next_page and len(transactions) < 10000:
                        params = next_page
                        # Sleep momentarily to respect rate limits
                        time.sleep(0.2)
                    else:
                        break
                else:
                    print(f"[-] BlockScout pagination stopped with status: {tx_response.status_code}")
                    break
                    
            counts['normal'] = len(transactions)
            print(f"[+] {chain.upper()} (BlockScout): {counts['normal']} transactions")
            
            return transactions, counts
        
        except Exception as e:
            print(f"[-] BlockScout {chain} error: {e}")
            return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        """Fetch single transaction by hash via BlockScout"""
        chain = chain.lower()
        if chain not in BlockScoutFetcher.BLOCKSCOUT_URLS:
            return None
            
        base_url = BlockScoutFetcher.BLOCKSCOUT_URLS[chain]
        
        try:
            tx_url = f"{base_url}/transactions/{tx_hash}"
            tx_response = requests.get(tx_url, timeout=15)
            
            if tx_response.status_code == 200:
                tx = tx_response.json()
                if tx and tx.get('hash'):
                    return {
                        'hash': tx.get('hash'),
                        'from': safe_checksum(tx.get('from', {}).get('hash') if isinstance(tx.get('from'), dict) else tx.get('from')),
                        'to': safe_checksum((tx.get('to', {}).get('hash') if isinstance(tx.get('to'), dict) else tx.get('to')) or (tx.get('created_contract', {}).get('hash') if isinstance(tx.get('created_contract'), dict) else tx.get('created_contract'))),
                        'value': float(tx.get('value', 0)) / 1e18 if tx.get('value') else 0.0,
                        'timestamp': tx.get('timestamp') or datetime.now().isoformat(),
                        'block': tx.get('block', 0),
                        'chain': chain
                    }
            return None
        except Exception as e:
            print(f"[-] BlockScout Tx details Error: {e}")
            return None

# ==================== BLOCKCYPHER API (Dogecoin) ====================

class BlockCypherFetcher:
    """Fetch Dogecoin transactions via BlockCypher API"""
    
    BASE_URL = "https://api.blockcypher.com/v1/doge/main"
    # Token provided by user: Limit 3 req/sec, 100/hr, 1000/day
    API_TOKEN =  os.getenv('BLOCKCYPHER_TOKEN', "280c03c6f8f34afb9d6f5e1b1fb1ab59")
    
    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        
        try:
            print(f"[+] Fetching Dogecoin data from BlockCypher for {address[:8]}...")
            
            # Pagination loop
            has_more = True
            before_bh = None
            total_fetched = 0
            MAX_FETCH = 500000 # Capture everything for the user's "1600-1700 txs" case
            
            while has_more and total_fetched < MAX_FETCH:
                # Construct URL - Try to fetch MAX in one go to save API calls
                # BlockCypher allows high limits with key
                # We use 2000 as it's a safe high limit common in APIs
                base = f"{BlockCypherFetcher.BASE_URL}/addrs/{address}/full?token={BlockCypherFetcher.API_TOKEN}&limit=2000"
                if before_bh:
                    base += f"&before={before_bh}"
                    
                print(f"[DEBUG] Fetching Batch: {base}")
                
                # Retry Logic (Exponential Backoff for Enterprise Reliability)
                max_retries = 5
                response = None
                
                for attempt in range(max_retries):
                    try:
                        # Rate limit protection (base delay)
                        time.sleep(2.0) 
                        response = requests.get(base, timeout=30)
                        
                        if response.status_code == 429:
                            # Exponential backoff: 5s, 10s, 20s, 40s, 80s
                            wait_time = (2 ** attempt) * 5 
                            print(f"[!] BlockCypher Rate Limit (429). Waiting {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue # Retry
                        
                        if response.status_code == 200:
                            break # Success
                        else:
                            print(f"[-] BlockCypher Error: {response.status_code} - {response.text[:100]}")
                            response = None
                            break # Don't retry other errors immediately
                            
                    except requests.exceptions.Timeout:
                        print(f"[!] Timeout. Retrying...")
                    except Exception as e:
                        print(f"[!] Network Error: {e}")
                        time.sleep(5)
                
                # If failed after all retries, break pagination loop
                if not response or response.status_code != 200:
                    print("[-] Failed to fetch BlockCypher batch after retries.")
                    break
                    
                data = response.json()
                batch = data.get('txs', [])
                
                if not batch:
                    has_more = False
                    break
                    
                for tx in batch:
                    # BlockCypher Time Format: 2021-04-16T14:45:04Z
                    tx_time_str = tx.get('confirmed', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
                    try:
                        dt = datetime.strptime(tx_time_str, '%Y-%m-%dT%H:%M:%SZ')
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                    # Calculate value flow and identify counterparty
                    total_input = 0
                    total_output = 0
                    flow = 'unknown'
                    
                    inputs = tx.get('inputs', [])
                    outputs = tx.get('outputs', [])
                    
                    # Check inputs (did we send?)
                    for curr_input in inputs:
                         if address in curr_input.get('addresses', []):
                             total_input += curr_input.get('output_value', 0)
                             
                    # Check outputs (did we receive?)
                    for curr_output in outputs:
                        if address in curr_output.get('addresses', []):
                            total_output += curr_output.get('value', 0)
                            
                    net_change = total_output - total_input
                    
                    sender = "Unknown"
                    receiver = "Unknown"
                    
                    if net_change > 0:
                        val = net_change / 1e8 # Satoshis to DOGE
                        flow = 'in'
                        # Sender is NOT us (inputs)
                        other_addresses = []
                        for inp in inputs:
                            for addr in inp.get('addresses', []):
                                if addr != address:
                                    other_addresses.append(addr)
                        sender = other_addresses[0] if other_addresses else "Unknown" # Take first for simplicity
                        receiver = address
                        
                    else:
                        val = abs(net_change) / 1e8
                        flow = 'out'
                        # Receiver is NOT us (outputs)
                        other_addresses = []
                        for out in outputs:
                            for addr in out.get('addresses', []):
                                if addr != address:
                                    other_addresses.append(addr)
                        receiver = other_addresses[0] if other_addresses else "Unknown"
                        sender = address
                        
                    transactions.append({
                        'hash': tx.get('hash'),
                        'timestamp': formatted_time,
                        'value': val,
                        'from': sender,
                        'to': receiver,
                        'chain': 'dogecoin',
                        'type': 'doge',
                        'block': tx.get('block_height')
                    })
                
                total_fetched += len(batch)
                
                # PAGINATION FIX:
                # API might return fewer than 'limit' if its internal max is lower (e.g. 50 vs 2000).
                # We should only stop if we got 0 results.
                if len(batch) == 0:
                    print("[-] Batch empty. Stopping.")
                    has_more = False
                else:
                    valid_blocks = [t.get('block_height', 999999999) for t in batch if isinstance(t, dict) and t.get('block_height')]
                    if not valid_blocks:
                        print("[-] No valid blocks in batch. Stopping.")
                        break
                    min_block = min(valid_blocks)
                    
                    # If we aren't making progress (min_block is same as before), we might be stuck or at end
                    if before_bh and min_block >= before_bh:
                         print("[-] Pagination stuck at block height. Stopping.")
                         has_more = False
                    else:     
                        before_bh = min_block
                        # Also check if we've fetched everything predicted by n_tx? 
                        # No, rely on clean batch end.
                        
                    # Also stop if batch is significantly small (e.g. < 5) AND likely end?
                    # No, let's keep going until 0 or limit.
                    # But if API returns 10 items every time, we need to keep going.
                    pass
                    
            counts['normal'] = len(transactions)
            print(f"[+] Dogecoin (BlockCypher): {counts['normal']} transactions (Paginated)")
                
            # Fallback to GetBlock.io if BlockCypher failed totally
            if len(transactions) == 0:
                 return MempoolFetcher._fetch_via_getblock(address)
                 
            return transactions, counts
            
        except Exception as e:
            print(f"[-] Dogecoin fetch error: {e}")
            return MempoolFetcher._fetch_via_getblock(address)

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        """Fetch single transaction by hash via BlockCypher"""
        try:
            base_url = f"{BlockCypherFetcher.BASE_URL}/txs/{tx_hash}?token={BlockCypherFetcher.API_TOKEN}"
            resp = requests.get(base_url, timeout=15)
            
            if resp.status_code == 200:
                tx = resp.json()
                
                total_input = sum([inp.get('output_value', 0) for inp in tx.get('inputs', [])])
                total_output = sum([out.get('value', 0) for out in tx.get('outputs', [])])
                fee = tx.get('fees', 0)
                
                # Try to determine generic from/to
                sender = tx.get('inputs', [{}])[0].get('addresses', ['Unknown'])[0] if tx.get('inputs') else 'Unknown'
                receiver = tx.get('outputs', [{}])[0].get('addresses', ['Unknown'])[0] if tx.get('outputs') else 'Unknown'
                
                tx_time_str = tx.get('confirmed', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
                try:
                    dt = datetime.strptime(tx_time_str, '%Y-%m-%dT%H:%M:%SZ')
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                return {
                    'hash': tx.get('hash'),
                    'timestamp': formatted_time,
                    'value': total_output / 1e8, # Satoshis to DOGE
                    'from': sender,
                    'to': receiver,
                    'chain': 'dogecoin',
                    'block': tx.get('block_height')
                }
            return None
        except Exception as e:
            print(f"[-] BlockCypher Tx details Error: {e}")
            return None

# ==================== ETHERSCAN v2 API (All EVM Chains) ====================

class EtherscanMultiChainFetcher:
    """
    Fetch transactions from EVM chains using Etherscan v2 API
    Uses SINGLE endpoint: https://api.etherscan.io/v2/api with chainid parameter
    """
    
    V2_ENDPOINT = 'https://api.etherscan.io/v2/api'
    
    CHAIN_CONFIGS = {
        'ethereum': {'chainid': 1, 'name': 'Ethereum Mainnet'},
        'hoodi': {'chainid': 560048, 'name': 'Hoodi Testnet'},
        'polygon': {'chainid': 137, 'name': 'Polygon Mainnet'},
        'amoy': {'chainid': 80002, 'name': 'Polygon Amoy Testnet'},
        'arbitrum': {'chainid': 42161, 'name': 'Arbitrum One Mainnet'},
        'arbitrum_sepolia': {'chainid': 421614, 'name': 'Arbitrum Sepolia Testnet'},
        'linea': {'chainid': 59144, 'name': 'Linea Mainnet'},
        'linea_sepolia': {'chainid': 59141, 'name': 'Linea Sepolia Testnet'},
        'blast': {'chainid': 81457, 'name': 'Blast Mainnet'},
        'blast_sepolia': {'chainid': 168587773, 'name': 'Blast Sepolia Testnet'},
        'bttc': {'chainid': 199, 'name': 'BitTorrent Chain Mainnet'},
        'bttc_testnet': {'chainid': 1029, 'name': 'BitTorrent Chain Testnet'},
        'celo': {'chainid': 42220, 'name': 'Celo Mainnet'},
        'celo_sepolia': {'chainid': 11142220, 'name': 'Celo Sepolia Testnet'},
        'fraxtal': {'chainid': 252, 'name': 'Fraxtal Mainnet'},
        'fraxtal_hoodi': {'chainid': 2523, 'name': 'Fraxtal Hoodi Testnet'},
        'gnosis': {'chainid': 100, 'name': 'Gnosis'},
        'mantle': {'chainid': 5000, 'name': 'Mantle Mainnet'},
        'mantle_sepolia': {'chainid': 5003, 'name': 'Mantle Sepolia Testnet'},
        'memecore': {'chainid': 4352, 'name': 'Memecore Mainnet'},
        'memecore_testnet': {'chainid': 43521, 'name': 'Memecore Testnet'},
        'moonbeam': {'chainid': 1284, 'name': 'Moonbeam Mainnet'},
        'moonriver': {'chainid': 1285, 'name': 'Moonriver Mainnet'},
        'moonbase': {'chainid': 1287, 'name': 'Moonbase Alpha Testnet'},
        'opbnb': {'chainid': 204, 'name': 'opBNB Mainnet'},
        'opbnb_testnet': {'chainid': 5611, 'name': 'opBNB Testnet'},
        'scroll': {'chainid': 534352, 'name': 'Scroll Mainnet'},
        'scroll_sepolia': {'chainid': 534351, 'name': 'Scroll Sepolia Testnet'},
        'taiko': {'chainid': 167000, 'name': 'Taiko Mainnet'},
        'taiko_hoodi': {'chainid': 167013, 'name': 'Taiko Hoodi'},
        'xdc': {'chainid': 50, 'name': 'XDC Mainnet'},
        'xdc_testnet': {'chainid': 51, 'name': 'XDC Apothem Testnet'},
        'swellchain': {'chainid': 1923, 'name': 'Swellchain Mainnet'},
        'swellchain_testnet': {'chainid': 1924, 'name': 'Swellchain Testnet'},
        'hyperevm': {'chainid': 999, 'name': 'HyperEVM Mainnet'},
        'katana': {'chainid': 747474, 'name': 'Katana Mainnet'},
        'katana_bokuto': {'chainid': 737373, 'name': 'Katana Bokuto'},
        'sei': {'chainid': 1329, 'name': 'Sei Mainnet'},
        'sei_testnet': {'chainid': 1328, 'name': 'Sei Testnet'},
        # P1 Chains via Etherscan V2
        'bnb': {'chainid': 56, 'name': 'BNB Chain (BSC)'},
        'bnb_testnet': {'chainid': 97, 'name': 'BNB Testnet'},
    }
    
    @staticmethod
    def _fetch_all_paginate_by_block(chain: str, address: str, action: str, startblock: int = 0) -> List[Dict]:
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        all_txs = []
        seen = set()
        offset = 10000  # Max allowed by Etherscan per page
        
        while True:
            params = {
                'chainid': config['chainid'],
                'module': 'account',
                'action': action,
                'address': address,
                'startblock': startblock,
                'endblock': 99999999,
                'page': 1,
                'offset': offset,
                'sort': 'asc', # Must be asc for block pagination to work correctly
                'apikey': ETHERSCAN_API_KEY
            }
            
            try:
                response = requests.get(EtherscanMultiChainFetcher.V2_ENDPOINT, params=params, timeout=15)
                data = response.json()
                
                if data.get('status') == '0' and data.get('message') != 'OK':
                    if data.get('result') != 'No transactions found':
                        print(f"[ETHERSCAN API] {data.get('message')} - {data.get('result')}")
                    break
                    
                page_results = data.get('result', []) or []
                if not page_results:
                    break
                    
                added_in_page = 0
                for tx in page_results:
                    thash = tx.get('hash')
                    if not thash:
                        continue
                    if thash not in seen:
                        seen.add(thash)
                        
                        # Normalize results
                        tx['chain'] = chain
                        
                        # Handle Contract Creations
                        if not tx.get('to') and tx.get('contractAddress'):
                            tx['to'] = tx['contractAddress']
                            
                        if 'timeStamp' in tx: # Normalize timestamp format
                            try:
                                tx['timestamp'] = datetime.utcfromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                        
                        # Normalize Value (Wei -> ETH)
                        if 'value' in tx:
                            try:
                                tx['value'] = float(tx['value']) / 1e18
                            except:
                                tx['value'] = 0.0
                        
                        # Fix Lowercase Casing bug by restoring Ethereum EIP-55 Checksum natively across Etherscan output.
                        if 'from' in tx:
                            tx['from'] = safe_checksum(tx.get('from'))
                        if 'to' in tx:
                            tx['to'] = safe_checksum(tx.get('to'))
                                
                        all_txs.append(tx)
                        added_in_page += 1
                        
                if len(page_results) < offset:
                    break
                    
                # Slide block window
                last_tx = page_results[-1]
                new_startblock = int(last_tx.get('blockNumber', startblock))
                if new_startblock == startblock and added_in_page == 0:
                    print("[ETHERSCAN API] Stuck on giant block, breaking.")
                    break
                startblock = new_startblock
                time.sleep(0.3)
                
            except Exception as e:
                print(f"[-] {config['name']} pagination error: {e}")
                break
                
        return all_txs

    @staticmethod
    def fetch_transactions(chain: str, address: str, include_internal: bool = True, 
                          include_token_transfers: bool = True, startblock: int = 0) -> Tuple[List[Dict], Dict]:
        
        chain = chain.lower()
        if chain not in EtherscanMultiChainFetcher.CHAIN_CONFIGS:
             return BlockScoutFetcher.fetch_transactions(chain, address)
        
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        if not ETHERSCAN_API_KEY:
            print(f"[!]  No Etherscan API key, using BlockScout for {config['name']}...")
            return BlockScoutFetcher.fetch_transactions(chain, address)
        
        try:
            print(f"[+] Fetching {config['name']} transactions via Etherscan v2 API concurrently (from block {startblock})...")
            
            import concurrent.futures

            def fetch_action(action_type):
                return EtherscanMultiChainFetcher._fetch_all_paginate_by_block(chain, address, action_type, startblock)
            
            # Map the needed actions to their respective keys
            fetch_plan = {'normal': 'txlist'}
            if include_internal:
                fetch_plan['internal'] = 'txlistinternal'
            if include_token_transfers:
                fetch_plan['token'] = 'tokentx'

            results = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Submit jobs
                futures_to_key = {
                    executor.submit(fetch_action, action): key 
                    for key, action in fetch_plan.items()
                }
                
                # Gather results
                for future in concurrent.futures.as_completed(futures_to_key):
                    k = futures_to_key[future]
                    try:
                        res = future.result()
                        results[k] = res
                        transactions.extend(res)
                        counts[k] = len(res)
                    except Exception as exc:
                        print(f"[-] Etherscan {k} threaded fetch generated an exception: {exc}")
                        counts[k] = 0
            
            total = sum(counts.values())
            print(f"[+] {config['name']}: {counts['normal']} normal, {counts['internal']} internal, {counts['token']} token ({total} total)")
            
            # Fallback to BlockScout if absolutely nothing was found (could be an API quirk)
            if total == 0 and startblock == 0:
                print(f"[!] Zero transactions found via Etherscan, attempting BlockScout fallback just in case...")
                bs_txs, bs_counts = BlockScoutFetcher.fetch_transactions(chain, address)
                if sum(bs_counts.values()) > 0:
                    return bs_txs, bs_counts
                    
            return transactions, counts
        
        except Exception as e:
            print(f"[-] {config['name']} fetch error: {e}")
            print(f"   Falling back to BlockScout...")
            return BlockScoutFetcher.fetch_transactions(chain, address)

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
         """Fetch transaction by hash on EVM chains. Relies on BlockScout fallback for generic tx queries"""
         print(f"[+] Proxying Etherscan TxHash to BlockScout...")
         return BlockScoutFetcher.fetch_by_tx_hash(chain, tx_hash)

# ==================== ALCHEMY API (EVM Layer 2s) ====================

class AlchemyEVMFetcher:
    """Fetch transactions via Alchemy's alchemy_getAssetTransfers JSON-RPC method"""
    
    ALCHEMY_URLS = {
        'beacon': 'https://eth-mainnet.g.alchemy.com/v2/',
        'beacon_sepolia': 'https://eth-sepolia.g.alchemy.com/v2/',
        'beacon_hoodi': 'https://eth-holesky.g.alchemy.com/v2/',
        'rootstock': 'https://rootstock-mainnet.g.alchemy.com/v2/',
        'rootstock_testnet': 'https://rootstock-testnet.g.alchemy.com/v2/',
        'scroll': 'https://scroll-mainnet.g.alchemy.com/v2/',
        'scroll_sepolia': 'https://scroll-sepolia.g.alchemy.com/v2/',
        'zksync': 'https://zksync-mainnet.g.alchemy.com/v2/',
        'zksync_sepolia': 'https://zksync-sepolia.g.alchemy.com/v2/',
        # P1 Chains via Alchemy
        'avalanche': 'https://avax-mainnet.g.alchemy.com/v2/',
        'avalanche_fuji': 'https://avax-fuji.g.alchemy.com/v2/',
        'optimism': 'https://opt-mainnet.g.alchemy.com/v2/',
        'optimism_sepolia': 'https://opt-sepolia.g.alchemy.com/v2/',
        'base': 'https://base-mainnet.g.alchemy.com/v2/',
        'base_sepolia': 'https://base-sepolia.g.alchemy.com/v2/',
        'polygon_zkevm': 'https://polygonzkevm-mainnet.g.alchemy.com/v2/',
        'polygon_zkevm_cardona': 'https://polygonzkevm-cardona.g.alchemy.com/v2/',
        
        # Extended Alchemy Networks via User Specification
        'worldchain': 'https://worldchain-mainnet.g.alchemy.com/v2/',
        'worldchain_sepolia': 'https://worldchain-sepolia.g.alchemy.com/v2/',
        'shape': 'https://shape-mainnet.g.alchemy.com/v2/',
        'shape_sepolia': 'https://shape-sepolia.g.alchemy.com/v2/',
        'arbitrum_nova': 'https://arbnova-mainnet.g.alchemy.com/v2/',
        'astar': 'https://astar-mainnet.g.alchemy.com/v2/',
        'zetachain': 'https://zetachain-mainnet.g.alchemy.com/v2/',
        'zetachain_testnet': 'https://zetachain-testnet.g.alchemy.com/v2/',
        'berachain': 'https://berachain-mainnet.g.alchemy.com/v2/',
        'berachain_bepolia': 'https://berachain-bepolia.g.alchemy.com/v2/',
        'zora': 'https://zora-mainnet.g.alchemy.com/v2/',
        'zora_sepolia': 'https://zora-sepolia.g.alchemy.com/v2/',
        'robinhood_testnet': 'https://robinhood-testnet.g.alchemy.com/v2/',
        'ronin': 'https://ronin-mainnet.g.alchemy.com/v2/',
        'ronin_saigon': 'https://ronin-saigon.g.alchemy.com/v2/',
        'plasma': 'https://plasma-mainnet.g.alchemy.com/v2/',
        'plasma_testnet': 'https://plasma-testnet.g.alchemy.com/v2/',
        'mythos': 'https://mythos-mainnet.g.alchemy.com/v2/',
        'settlus': 'https://settlus-mainnet.g.alchemy.com/v2/',
        'settlus_sepolia': 'https://settlus-septestnet.g.alchemy.com/v2/',
        'megaeth': 'https://megaeth-mainnet.g.alchemy.com/v2/',
        'megaeth_testnet': 'https://megaeth-testnet.g.alchemy.com/v2/',
        'citrea': 'https://citrea-mainnet.g.alchemy.com/v2/',
        'citrea_testnet': 'https://citrea-testnet.g.alchemy.com/v2/',
        'tea_sepolia': 'https://tea-sepolia.g.alchemy.com/v2/',
        'gensyn_testnet': 'https://gensyn-testnet.g.alchemy.com/v2/',
        'arc_testnet': 'https://arc-testnet.g.alchemy.com/v2/',
        'story': 'https://story-mainnet.g.alchemy.com/v2/',
        'story_aeneid': 'https://story-aeneid.g.alchemy.com/v2/',
        'clankermon': 'https://clankermon-mainnet.g.alchemy.com/v2/',
        'humanity': 'https://humanity-mainnet.g.alchemy.com/v2/',
        'humanity_testnet': 'https://humanity-testnet.g.alchemy.com/v2/',
        'risa_testnet': 'https://risa-testnet.g.alchemy.com/v2/',
        'tempo_testnet': 'https://tempo-testnet.g.alchemy.com/v2/',
        'tempo_moderato': 'https://tempo-moderato.g.alchemy.com/v2/',
        'hyperliquid': 'https://hyperliquid-mainnet.g.alchemy.com/v2/',
        'hyperliquid_testnet': 'https://hyperliquid-testnet.g.alchemy.com/v2/',
        'lens': 'https://lens-mainnet.g.alchemy.com/v2/',
        'lens_sepolia': 'https://lens-sepolia.g.alchemy.com/v2/',
        'worldmobilechain': 'https://worldmobilechain-mainnet.g.alchemy.com/v2/',
        'worldmobile_testnet': 'https://worldmobile-testnet.g.alchemy.com/v2/',
        'frax': 'https://frax-mainnet.g.alchemy.com/v2/',
        'frax_sepolia': 'https://frax-sepolia.g.alchemy.com/v2/',
        'ink': 'https://ink-mainnet.g.alchemy.com/v2/',
        'ink_sepolia': 'https://ink-sepolia.g.alchemy.com/v2/',
        'celestiabridge': 'https://celestiabridge-mainnet.g.alchemy.com/v2/',
        'celestiabridge_mocha': 'https://celestiabridge-mocha.g.alchemy.com/v2/',
        'unichain': 'https://unichain-mainnet.g.alchemy.com/v2/',
        'unichain_sepolia': 'https://unichain-sepolia.g.alchemy.com/v2/',
        'syndicate': 'https://synd-mainnet.g.alchemy.com/v2/',
        'superseed': 'https://superseed-mainnet.g.alchemy.com/v2/',
        'superseed_sepolia': 'https://superseed-sepolia.g.alchemy.com/v2/',
        'rise_testnet': 'https://rise-testnet.g.alchemy.com/v2/',
        'monad': 'https://monad-mainnet.g.alchemy.com/v2/',
        'monad_testnet': 'https://monad-testnet.g.alchemy.com/v2/',
        'flow': 'https://flow-mainnet.g.alchemy.com/v2/',
        'flow_testnet': 'https://flow-testnet.g.alchemy.com/v2/',
        'degen': 'https://degen-mainnet.g.alchemy.com/v2/',
        'polynomial': 'https://polynomial-mainnet.g.alchemy.com/v2/',
        'polynomial_sepolia': 'https://polynomial-sepolia.g.alchemy.com/v2/',
        'mode': 'https://mode-mainnet.g.alchemy.com/v2/',
        'mode_sepolia': 'https://mode-sepolia.g.alchemy.com/v2/',
        'apechain': 'https://apechain-mainnet.g.alchemy.com/v2/',
        'apechain_curtis': 'https://apechain-curtis.g.alchemy.com/v2/',
        'anime': 'https://anime-mainnet.g.alchemy.com/v2/',
        'anime_sepolia': 'https://anime-sepolia.g.alchemy.com/v2/',
        'metis': 'https://metis-mainnet.g.alchemy.com/v2/',
        'sonic': 'https://sonic-mainnet.g.alchemy.com/v2/',
        'sonic_testnet': 'https://sonic-testnet.g.alchemy.com/v2/',
        'sonic_blaze': 'https://sonic-blaze.g.alchemy.com/v2/',
        'xmtp_ropsten': 'https://xmtp-ropsten.g.alchemy.com/v2/',
        'adi': 'https://adi-mainnet.g.alchemy.com/v2/',
        'adi_testnet': 'https://adi-testnet.g.alchemy.com/v2/',
        'abstract': 'https://abstract-mainnet.g.alchemy.com/v2/',
        'abstract_testnet': 'https://abstract-testnet.g.alchemy.com/v2/',
        'crossfi': 'https://crossfi-mainnet.g.alchemy.com/v2/',
        'crossfi_testnet': 'https://crossfi-testnet.g.alchemy.com/v2/',
        'soneium': 'https://soneium-mainnet.g.alchemy.com/v2/',
        'soneium_minato': 'https://soneium-minato.g.alchemy.com/v2/',
        'stable': 'https://stable-mainnet.g.alchemy.com/v2/',
        'stable_testnet': 'https://stable-testnet.g.alchemy.com/v2/'
    }

    @staticmethod
    def _fetch_transfers(chain: str, address: str, direction: str) -> List[Dict]:
        """Fetch incoming or outgoing transfers via alchemy_getAssetTransfers"""
        if not ALCHEMY_API_KEY:
            print("[!] Missing ALCHEMY_API_KEY")
            return []

        base_url = AlchemyEVMFetcher.ALCHEMY_URLS.get(chain)
        if not base_url:
            return []
            
        url = f"{base_url}{ALCHEMY_API_KEY}"
        all_txs = []
        page_key = None
        
        while True:
            params = {
                "fromBlock": "0x0",
                "toBlock": "latest",
                "category": ["external", "erc20", "erc721", "erc1155"],
                "withMetadata": True,
                "excludeZeroValue": False,
                "maxCount": "0x3E8" # 1000 max per page
            }
            
            if direction == "from":
                params["fromAddress"] = address
            else:
                params["toAddress"] = address
                
            if page_key:
                params["pageKey"] = page_key
                
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "alchemy_getAssetTransfers",
                "params": [params]
            }
            
            headers = {"accept": "application/json", "content-type": "application/json"}
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                data = response.json()
                
                error_payload = data.get('error')
                if error_payload:
                    err_msg = str(error_payload)
                    if isinstance(error_payload, dict):
                        err_msg = error_payload.get('message', err_msg)
                    print(f"[-] Alchemy query error on {chain}: {err_msg}")
                    break
                
                result = data.get('result') or {}
                transfers = result.get('transfers', [])
                
                for tx in transfers:
                    meta = tx.get('metadata') or {}
                    timestamp_str = meta.get('blockTimestamp')
                    formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if timestamp_str:
                        try:
                            # 2023-10-01T12:00:00Z
                            if timestamp_str.endswith('Z'):
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
                            else:
                                dt = datetime.fromisoformat(timestamp_str.split('.')[0])
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                            
                    block_num_hex = tx.get('blockNum') or '0x0'
                    all_txs.append({
                        'hash': tx.get('hash'),
                        'from': tx.get('from', 'Unknown') or 'Unknown',
                        'to': tx.get('to', 'Unknown') or 'Unknown',
                        'value': tx.get('value') or 0.0,
                        'timestamp': formatted_time,
                        'block': int(block_num_hex, 16),
                        'chain': chain,
                        'type': tx.get('category', 'transfer'),
                        'uniqueId': tx.get('uniqueId')
                    })
                    
                page_key = result.get('pageKey')
                if not page_key:
                    break
                    
                time.sleep(0.1) # Rate limit protection
            except Exception as e:
                print(f"[-] Alchemy query error on {chain}: {e}")
                break
                
        return all_txs

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        chain = chain.lower()
        if chain not in AlchemyEVMFetcher.ALCHEMY_URLS:
            return [], {'normal': 0}
            
        print(f"[+] Fetching Alchemy EVM data sequentially for {chain} (Bi-Directional)...")
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_out = executor.submit(AlchemyEVMFetcher._fetch_transfers, chain, address, "from")
            future_in = executor.submit(AlchemyEVMFetcher._fetch_transfers, chain, address, "to")
            
            outgoing = future_out.result()
            incoming = future_in.result()
            
        combined = outgoing + incoming
        
        # Deduplicate using uniqueId
        unique_txs = {}
        for tx in combined:
            uid = tx.get('uniqueId')
            if not uid:
                uid = f"{tx.get('hash')}_{tx.get('from')}_{tx.get('to')}_{tx.get('value')}"
            unique_txs[uid] = tx
        
        final_list = list(unique_txs.values())
        
        # Sort chronologically by timestamp
        final_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        for tx in final_list:
            tx['from'] = safe_checksum(tx['from'])
            tx['to'] = safe_checksum(tx['to'])
            
            t = tx.get('type', 'transfer')
            if t in ('erc20', 'erc721', 'erc1155'):
                counts['token'] += 1
            elif t == 'internal':
                counts['internal'] += 1
            else:
                counts['normal'] += 1
                
        total = counts['normal'] + counts['internal'] + counts['token']
        print(f"[+] {chain.upper()} (Alchemy): {total} unique transfers found")
        return final_list, counts
        
    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        """Alchemy fetch by hash via eth_getTransactionByHash"""
        chain = chain.lower()
        if chain not in AlchemyEVMFetcher.ALCHEMY_URLS or not ALCHEMY_API_KEY:
            return None
            
        try:
            url = f"{AlchemyEVMFetcher.ALCHEMY_URLS[chain]}{ALCHEMY_API_KEY}"
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_getTransactionByHash",
                "params": [tx_hash]
            }
            response = requests.post(url, json=payload, timeout=10)
            tx = response.json().get('result')
            
            if tx:
                # eth_getTransactionByHash does not return timestamps natively in EVM APIs,
                # we must fetch the block it was mined in to get the timestamp.
                block_hex = tx.get('blockNumber')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if block_hex:
                    block_payload = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "eth_getBlockByNumber",
                        "params": [block_hex, False]
                    }
                    block_resp = requests.post(url, json=block_payload, timeout=10)
                    block_data = block_resp.json().get('result', {})
                    ts_hex = block_data.get('timestamp')
                    if ts_hex:
                        timestamp = datetime.fromtimestamp(int(ts_hex, 16)).strftime('%Y-%m-%d %H:%M:%S')

                val_hex = tx.get('value', '0x0')
                value_eth = int(val_hex, 16) / 1e18 if val_hex else 0.0
                
                # Restore UI Checksoum Caps
                try:
                    from web3 import Web3
                    w3 = Web3()
                    def checksum(addr):
                        try:
                            if addr and addr != 'Unknown' and addr.startswith('0x'):
                                return w3.to_checksum_address(addr.lower())
                        except:
                            pass
                        return addr
                except ImportError:
                    def checksum(addr): return addr
                
                return {
                    'hash': tx.get('hash'),
                    'from': checksum(tx.get('from', 'Unknown')),
                    'to': checksum(tx.get('to', 'Unknown')),
                    'value': value_eth,
                    'timestamp': timestamp,
                    'block': int(block_hex, 16) if block_hex else 0,
                    'chain': chain
                }
            return None
        except Exception as e:
            print(f"[-] Alchemy Hash Fetch error: {e}")
            return None


class AlchemyAptosFetcher:
    """Fetch Aptos transactions via Alchemy REST endpoints"""
    
    APTOS_URLS = {
        'aptos': 'https://aptos-mainnet.g.alchemy.com/v2/',
        'aptos_testnet': 'https://aptos-testnet.g.alchemy.com/v2/'
    }

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        chain = chain.lower()
        if chain not in AlchemyAptosFetcher.APTOS_URLS or not ALCHEMY_API_KEY:
            return [], {'normal': 0}
            
        base_url = AlchemyAptosFetcher.APTOS_URLS[chain]
        # Alchemy Aptos REST URL setup
        url = f"{base_url}{ALCHEMY_API_KEY}/v1/accounts/{address}/transactions"
        
        all_txs = []
        limit = 100
        start_version = None
        
        # Aptos is a high throughput chain, grab latest 200 txs to avoid heavy REST loops
        for _ in range(2): 
            params = {"limit": limit}
            if start_version:
                params["start"] = start_version
                
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                if not data:
                    break
                    
                for tx in data:
                    # Aptos specific transaction schema
                    sender = tx.get('sender', 'Unknown')
                    
                    # Aptos payload varies widely, try to extract 'to' from entry function payloads if possible
                    receiver = 'Unknown'
                    payload = tx.get('payload', {})
                    if payload.get('type') == 'entry_function_payload':
                        args = payload.get('arguments', [])
                        # A generic heuristic to find an address-like string in arguments
                        for arg in args:
                            if isinstance(arg, str) and arg.startswith('0x') and len(arg) > 40:
                                receiver = arg
                                break
                    
                    # Value extraction from events if it's a coin transfer
                    value = 0.0
                    for event in tx.get('events', []):
                        if 'WithdrawEvent' in event.get('type', ''):
                            try:
                                val_str = event.get('data', {}).get('amount')
                                if val_str:
                                    value = float(val_str) / 1e8 # APT decimal assumption
                                    break
                            except:
                                pass
                                
                    timestamp = tx.get('timestamp')
                    formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if timestamp:
                        try:
                            formatted_time = datetime.fromtimestamp(int(timestamp) / 1000000).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                            
                    all_txs.append({
                        'hash': tx.get('hash'),
                        'from': sender,
                        'to': receiver,
                        'value': value,
                        'timestamp': formatted_time,
                        'block': int(tx.get('version', 0)),
                        'chain': chain,
                        'type': tx.get('type', 'user_transaction')
                    })
                    
                # Pagination logic for Aptos REST
                start_version = data[-1].get('version')
                if not start_version:
                    break
                    
                # Decrement start version for next page (Aptos orders chronologically normally)
                # But since we want to go backward in time, we actually need to use 'start' parameter differently.
                # Since Alchemy returns earliest first if `start` rests, we must reverse at the end.
            except Exception as e:
                print(f"[-] Aptos fetch error on {chain}: {e}")
                break
                
        # Deduplicate and sort descending by timestamp
        unique_txs = {tx['hash']: tx for tx in all_txs if tx.get('hash')}
        final_list = list(unique_txs.values())
        final_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        counts = {'normal': len(final_list)}
        print(f"[+] {chain.upper()}: {counts['normal']} transactions found")
        return final_list, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        chain = chain.lower()
        if chain not in AlchemyAptosFetcher.APTOS_URLS or not ALCHEMY_API_KEY:
            return None
            
        base_url = AlchemyAptosFetcher.APTOS_URLS[chain]
        url = f"{base_url}{ALCHEMY_API_KEY}/v1/transactions/by_hash/{tx_hash}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                tx = response.json()
                
                sender = tx.get('sender', 'Unknown')
                receiver = 'Unknown'
                payload = tx.get('payload', {})
                if payload.get('type') == 'entry_function_payload':
                    args = payload.get('arguments', [])
                    for arg in args:
                        if isinstance(arg, str) and arg.startswith('0x') and len(arg) > 40:
                            receiver = arg
                            break
                            
                value = 0.0
                for event in tx.get('events', []):
                    if 'WithdrawEvent' in event.get('type', ''):
                        try:
                            val_str = event.get('data', {}).get('amount')
                            if val_str:
                                value = float(val_str) / 1e8 
                                break
                        except:
                            pass
                            
                timestamp = tx.get('timestamp')
                formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if timestamp:
                    try:
                        formatted_time = datetime.fromtimestamp(int(timestamp) / 1000000).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                        
                return {
                    'hash': tx.get('hash'),
                    'from': sender,
                    'to': receiver,
                    'value': value,
                    'timestamp': formatted_time,
                    'block': int(tx.get('version', 0)),
                    'chain': chain
                }
            return None
        except Exception as e:
            print(f"[-] Aptos Hash Fetch error: {e}")
            return None

# ==================== BITCOIN (Mempool.space) ====================

class MempoolFetcher:
    """Fetch Bitcoin transactions via Mempool.space (Free, No Key)"""
    
    BASE_URL = "https://mempool.space/api"
    
    @staticmethod
    def _fetch_via_getblock(address: str) -> Tuple[List[Dict], Dict]:
        """Fallback: GetBlock.io RPC (Limited functionality without full node access)"""
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        getblock_key = os.getenv('GETBLOCK_DOGE_KEY')
        endpoint = os.getenv('GETBLOCK_ENDPOINT')
        
        if not getblock_key and not endpoint:
            print("[!] No GETBLOCK_DOGE_KEY or GETBLOCK_ENDPOINT in .env. Falling back to empty response.")
            return [], counts
            
        print(f"[GetBlock.io] Attempting fallback for {address}...")
        url = endpoint if endpoint else f"https://go.getblock.io/{getblock_key}/"
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "doge_bb_getAddress",
            "params": [address, {"details": "txs"}],
            "id": "getblock.io"
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'result' in data and 'transactions' in data['result']:
                    raw_txs = data['result']['transactions']
                    for tx in raw_txs:
                        # Parse Blockbook format
                        timestamp = tx.get('blockTime', int(time.time()))
                        val = abs(float(tx.get('value', 0))) / 1e8 # Satoshis to DOGE
                        
                        transactions.append({
                            'hash': tx.get('txid'),
                            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            'value': val,
                            'from': 'Unknown' if float(tx.get('value', 0)) > 0 else address, 
                            'to': address if float(tx.get('value', 0)) > 0 else 'Unknown',
                            'chain': 'dogecoin',
                            'type': 'doge'
                        })
                    counts['normal'] = len(transactions)
                    print(f"[+] Dogecoin (GetBlock): {counts['normal']} transactions")
                    return transactions, counts
            else:
                 print(f"[-] GetBlock.io returned status {resp.status_code}")
        except Exception as e:
             print(f"[-] GetBlock.io Error: {e}")
             
        return [], counts
    
    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        
        try:
            print(f"[+] Fetching Bitcoin data from Mempool.space for {address[:8]}...")
            url = f"{MempoolFetcher.BASE_URL}/address/{address}/txs"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                tx_data = response.json()
                
                for tx in tx_data:
                    # Parse Bitcoin transaction
                    tx_hash = tx.get('txid')
                    status = tx.get('status', {})
                    block_time = status.get('block_time', int(time.time()))
                    
                    # Calculate value flow relative to this address
                    value = 0
                    flow_type = 'unknown'
                    
                    # Check inputs (sending)
                    inputs_val = sum(inp.get('prevout', {}).get('value', 0) for inp in tx.get('vin', []) 
                                   if inp.get('prevout', {}).get('scriptpubkey_address') == address)
                    
                    # Check outputs (receiving)
                    outputs_val = sum(out.get('value', 0) for out in tx.get('vout', []) 
                                    if out.get('scriptpubkey_address') == address)
                    
                    if inputs_val > 0:
                        value = (inputs_val - outputs_val) / 1e8 # Sent amount (Satoshis -> BTC)
                        flow_type = 'out'
                        counterparty = "Multiple Inputs" # Simplified
                    else:
                        value = outputs_val / 1e8 # Received amount
                        flow_type = 'in'
                        counterparty = "Multiple Outputs"
                    
                    transactions.append({
                        'hash': tx_hash,
                        'timestamp': datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S'),
                        'value': abs(value),
                        'from': address if flow_type == 'out' else 'Incoming',
                        'to': 'Outgoing' if flow_type == 'out' else address,
                        'chain': 'bitcoin',
                        'flow': flow_type
                    })
                
                counts['normal'] = len(transactions)
                print(f"[+] Bitcoin (Mempool): {counts['normal']} transactions")
                return transactions, counts
            else:
                print(f"[-] Mempool API error: {response.status_code}")
                
            return transactions, counts
            
        except Exception as e:
            print(f"[-] Bitcoin fetch error: {e}")
            return [], counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        """Fetch single transaction by hash via Mempool.space"""
        try:
            url = f"{MempoolFetcher.BASE_URL}/tx/{tx_hash}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                tx = response.json()
                status = tx.get('status', {})
                block_time = status.get('block_time', int(time.time()))
                
                # Mempool gives us inputs and outputs. We can try to sum them.
                total_input = sum(inp.get('prevout', {}).get('value', 0) for inp in tx.get('vin', []))
                total_output = sum(out.get('value', 0) for out in tx.get('vout', []))
                
                # Guess sender/receiver (first input/output)
                sender = tx.get('vin', [{}])[0].get('prevout', {}).get('scriptpubkey_address', 'Unknown')
                receiver = tx.get('vout', [{}])[0].get('scriptpubkey_address', 'Unknown')

                return {
                    'hash': tx.get('txid'),
                    'timestamp': datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'value': total_output / 1e8, # Satoshis to BTC
                    'from': sender,
                    'to': receiver,
                    'chain': 'bitcoin',
                    'block': status.get('block_height', 'Pending')
                }
            return None
        except Exception as e:
            print(f"[-] Bitcoin Tx details Error: {e}")
            return None


# ==================== SOLANA (Solscan v2) ====================
class SolanaFetcher:
    """Fetch Solana transactions via Solscan Public API v2 (Official) or RPC Fallback"""
    
    # api-v2 Verified Public API
    BASE_URL = "https://api-v2.solscan.io/v2" 
    # Use Helius as primary RPC
    RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}" 
    
    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        """
        Fetch Solana transactions via Helius Enhanced API (Primary) or Solscan API.
        """
        print(f"[Solana] Fetching transactions for {address}...")
        
        # 1. Try Helius Enhanced API first (Best for history)
        try:
            print(f"[Solana] Initializing Helius Enhanced Fetch for {address}...")
            transactions, counts = SolanaFetcher._fetch_helius_enhanced(address)
            if transactions:
                # print(f"[+] Helius Enhanced API: {len(transactions)} transactions found")
                return transactions, counts
        except Exception as e:
            print(f"[!] Helius Enhanced API failed: {e}. Trying Solscan fallback...")

        # 2. Solscan Fallback (Internal api-v2 or Pro)
        transactions = []
        counts = {'normal': 0, 'token': 0}
        
        headers = {
            "token": SOLANA_API_KEY, 
            "accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Origin": "https://solscan.io",
            "Referer": "https://solscan.io/"
        }
        
        # If key looks like JWT, use Bearer
        if len(SOLANA_API_KEY) > 50:
             headers = {
                "Authorization": f"Bearer {SOLANA_API_KEY}",
                "accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                "Origin": "https://solscan.io",
                "Referer": "https://solscan.io/"
            }
        
        try:
            # Try Account Transaction API (Singular)
            url = f"{SolanaFetcher.BASE_URL}/account/transaction?address={address}&page_size=100"
            resp = requests.get(url, headers=headers, timeout=15)
            
            # If authorized failed, try Public API
            if resp.status_code in [401, 403]:
                print(f"[!]  Solscan {resp.status_code}. Trying Public API fallback...")
                public_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                    "Referer": "https://solscan.io/"
                }
                # Try Solscan Public API V2
                url = f"https://api.solscan.io/account/transactions?address={address}&limit=50"
                resp = requests.get(url, headers=public_headers, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get('data', [])
                # The api-v2 returns a wrapper 'data' which is usually a list
                # Handle V1 list response or V2 data wrapper
                if isinstance(data, list): items = data
                
                if isinstance(items, list):
                    if len(items) > 0:
                        print(f"[DEBUG SOLANA] First raw item: {items[0]}")
                    for item in items:
                        tx_hash = item.get('tx_hash') or item.get('encId') or item.get('txHash')
                        block_time = item.get('block_time', item.get('blockTime', 0))
                        
                        val = 0.0
                        flow = 'unknown'
                        
                        # Try to detect SOL balance change
                        # Support both V1 (sol_bal_change) and V2 (changeAmount, amount) fields
                        if 'changeAmount' in item:
                             val = abs(float(item['changeAmount'])) / 1e9 # Usually lamports
                        elif 'parsedInstruction' in item:
                             # Try to find amount in parsed instruction
                             try:
                                 params = item.get('parsedInstruction', {}).get('params', {})
                                 if 'amount' in params:
                                     val = float(params['amount']) / 1e9
                                 elif 'uiAmount' in params: # Sometimes pre-normalized
                                     val = float(params['uiAmount'])
                             except:
                                 pass
                        elif 'sol_bal_change' in item:
                            change = float(item['sol_bal_change']) / 1e9
                            if change > 0:
                                val = change
                                flow = 'in'
                            else:
                                val = abs(change)
                                flow = 'out'
                        elif 'lamport' in item:
                             val = float(item['lamport']) / 1e9
                        
                        # Try to get real addresses from parsing
                        sender = "Unknown"
                        receiver = "Interaction"
                        
                        # V2 Parsing Strategy
                        if 'signer' in item:
                            sender = item['signer'][0] if isinstance(item['signer'], list) and item['signer'] else item.get('signer', 'Unknown')
                        
                        # Fallback parsing
                        if sender == "Unknown" and 'parsedInstruction' in item:
                             # Try account keys
                             pass # implemented below
                             
                        # Logic to preserve CASE
                        # If flow is OUT, sender is US (use input address but try to find it in keys to get correct case?)
                        # Actually, if we use the API response, it should be correct case.
                        
                        transactions.append({
                            'hash': tx_hash,
                            'timestamp': datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S'),
                            'value': val,
                            'from': sender if sender != "Unknown" else (address if flow == 'out' else 'Interaction'), 
                            'to': receiver if receiver != "Interaction" else (address if flow == 'in' else 'Interaction'), 
                            'chain': 'solana',
                            'type': 'sol'
                        })
                    
                    counts['normal'] = len(transactions)
                    print(f"[+] Solscan: {len(transactions)} transactions found")
                    return transactions, counts
            
        except Exception as e:
            print(f"[!] Solscan API Error: {e}")

        # 3. Last Resort: Public Solana RPC
        print("[!] Helius and Solscan failed. Attempting publicnode last-resort fallback...")
        return SolanaFetcher._fetch_rpc_signatures(address, url="https://solana-rpc.publicnode.com")

    @staticmethod
    def _fetch_helius_enhanced(address: str) -> Tuple[List[Dict], Dict]:
        """Fetch transactions via Helius Enhanced API (v0 History)"""
        url = f"https://api-mainnet.helius-rpc.com/v0/addresses/{address}/transactions/?api-key={HELIUS_API_KEY}"
        transactions = []
        counts = {'normal': 0, 'token': 0}

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for tx in data:
                    tx_hash = tx.get('signature')
                    block_time = tx.get('timestamp', 0)
                    desc = tx.get('description', '')
                    fee_payer = tx.get('feePayer', 'Unknown')
                    
                    val = 0.0
                    sender = "Unknown"
                    receiver = "Interaction"
                    
                    # 1. Check accountData for net balance change to determine magnitude and direction
                    net_change = 0
                    for ad in tx.get('accountData', []):
                        if ad.get('account') == address:
                            net_change = ad.get('nativeBalanceChange', 0)
                            break
                    
                    if net_change < 0:
                        sender = address
                        receiver = "Multiple Outputs"
                        val = abs(net_change) / 1e9
                    elif net_change > 0:
                        sender = "Multiple Inputs"
                        receiver = address
                        val = net_change / 1e9

                    # 2. Refine sender/receiver by looking for direct transfers involving our address
                    native_transfers = tx.get('nativeTransfers', [])
                    
                    if net_change > 0: # We are receiving
                        # Look for who sent it to us
                        for nt in native_transfers:
                            if nt.get('toUserAccount') == address:
                                sender = nt.get('fromUserAccount')
                                # If there are multiple direct transfers to us, this picks the last one (or we could sum)
                                # but usually one primary sender for the main value.
                        if sender == "Multiple Inputs" and fee_payer != address:
                            sender = fee_payer # Better fallback than "Multiple"
                    
                    elif net_change < 0: # We are sending
                        # Look for who we sent it to
                        for nt in native_transfers:
                            if nt.get('fromUserAccount') == address:
                                receiver = nt.get('toUserAccount')
                        if receiver == "Multiple Outputs":
                             # If we can't find a single recipient, we keep "Multiple Outputs"
                             pass

                    # 3. Special case: if net_change is 0 but there are transfers (unlikely for SOL but good for tokens)
                    if net_change == 0 and native_transfers:
                        for nt in native_transfers:
                            if nt.get('toUserAccount') == address:
                                sender = nt.get('fromUserAccount')
                                receiver = address
                                val = nt.get('amount', 0) / 1e9
                                break
                            if nt.get('fromUserAccount') == address:
                                sender = address
                                receiver = nt.get('toUserAccount')
                                val = nt.get('amount', 0) / 1e9
                                break

                    transactions.append({
                        'hash': tx_hash,
                        'timestamp': datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S') if block_time else 'Unknown',
                        'value': val,
                        'from': sender,
                        'to': receiver,
                        'chain': 'solana',
                        'type': 'sol',
                        'description': desc
                    })
                
                counts['normal'] = len(transactions)
                print(f"[+] Helius Enhanced: {len(transactions)} transactions found")
                return transactions, counts
            else:
                print(f"[!] Helius Enhanced Error: {resp.status_code}")
                return [], counts
        except Exception as e:
            print(f"[!] Helius Enhanced Exception: {e}")
            return [], counts

    @staticmethod
    def _fetch_rpc_signatures(address: str, limit: int = 1000, url: str = None) -> Tuple[List[Dict], Dict]:
        """Fetch signatures from Solana RPC (Helius or Public)"""
        if not url: url = SolanaFetcher.RPC_URL
        # Add User-Agent to avoid 403 blocks from public RPC nodes
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        transactions = [] # Initialize transactions list for this fallback method
        counts = {'normal': 0, 'token': 0}

        # Fallback to RPC logic

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                address,
                {"limit": 100} # Increased limit for better utility, but safe for initial fetch
            ]
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            data = resp.json()
            
            if 'result' in data:
                signatures_raw = data['result']
                
                # 1. Populate basic info first (Guaranteed to return something)
                tx_map = {}
                for item in signatures_raw:
                    sig = item.get('signature')
                    ts = item.get('blockTime', 0)
                    tx_obj = {
                        'hash': sig,
                        'timestamp': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else 'Unknown',
                        'value': 0.0, # Default to 0
                        'from': 'Solana Address', 
                        'to': 'Interaction', 
                        'chain': 'solana',
                        'type': 'sol'
                    }
                    transactions.append(tx_obj)
                    tx_map[sig] = tx_obj

                # 2. Try to enrich with details (Best Effort)
                try:
                    sigs_to_fetch = [x['signature'] for x in signatures_raw][:25] # Increased to 25
                    
                    if sigs_to_fetch:
                        print(f"[+] Fetching details for {len(sigs_to_fetch)} txs (Sequential with Retry)...")
                        
                        import time
                        for idx, sig in enumerate(sigs_to_fetch):
                            # Sequential fetch with Retry Logic
                            max_retries = 5 # Increased from 3
                            for attempt in range(max_retries):
                                try:
                                    payload = {
                                        "jsonrpc": "2.0",
                                        "id": 1,
                                        "method": "getTransaction",
                                        "params": [
                                            sig,
                                            {"encoding": "json", "maxSupportedTransactionVersion": 0}
                                        ]
                                    }
                                    
                                    # Increased timeout to 10s
                                    resp = requests.post(url, json=payload, headers=headers, timeout=10)
                                    
                                    if resp.status_code == 429:
                                        wait_time = (2 ** attempt) * 3 # Exponential: 3s, 6s, 12s, 24s...
                                        print(f"[!] Rate limited (429) for {sig[:8]}... attempt {attempt+1}/{max_retries}, waiting {wait_time}s...")
                                        time.sleep(wait_time)
                                        continue
                                        
                                    item = resp.json()
                                    
                                    if 'result' in item and item['result']:
                                        tx_res = item['result']
                                        meta = tx_res.get('meta', {})
                                        
                                        # 1. Parse Account Keys (Addresses)
                                        keys = []
                                        tx_data = tx_res.get('transaction', {})
                                        if 'message' in tx_data:
                                            msg = tx_data['message']
                                            if 'accountKeys' in msg:
                                                raw_keys = msg['accountKeys']
                                                if len(raw_keys) > 0:
                                                    if isinstance(raw_keys[0], str):
                                                        keys = raw_keys
                                                    elif isinstance(raw_keys[0], dict):
                                                        keys = [k.get('pubkey') for k in raw_keys]
                                        
                                        sender = keys[0] if len(keys) > 0 else "Unknown"
                                        receiver = keys[1] if len(keys) > 1 else "Interaction"
                                        
                                        # 3. Calculate Value
                                        pre_bal = meta.get('preBalances', [0])[0]
                                        post_bal = meta.get('postBalances', [0])[0]
                                        val = abs(pre_bal - post_bal) / 1e9
                                        
                                        if sig in tx_map:
                                            tx_map[sig]['value'] = val
                                            tx_map[sig]['from'] = sender
                                            tx_map[sig]['to'] = receiver
                                    
                                    # Failures in 'result' (e.g. null) should not retry if it's 200 OK
                                    break
                                    
                                except Exception as sub_e:
                                    # Network error, wait and retry
                                    print(f"[!] Failed to fetch detail for {sig}: {sub_e}")
                                    time.sleep(2)
                            
                            # Increased base delay to 1.0s to be very safe
                            time.sleep(1.0)

                except Exception as e:
                    print(f"[!] Solana Sequential RPC failed: {e}")

                print(f"[+] Solana RPC: {len(transactions)} transactions found")
                counts['normal'] = len(transactions)
                return transactions, counts
            else:
                print(f"[-] Solana RPC Error: {data.get('error', {})}")
                return [], counts
        except Exception as e:
            print(f"[-] Solana RPC Exception: {e}")
            return [], counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        """Fetch single transaction by hash via Solana RPC"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                tx_hash,
                {"encoding": "json", "maxSupportedTransactionVersion": 0}
            ]
        }
        
        try:
            resp = requests.post(SolanaFetcher.RPC_URL, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                item = resp.json()
                if 'result' in item and item['result']:
                    tx_res = item['result']
                    meta = tx_res.get('meta', {})
                    
                    # Parse Account Keys
                    keys = []
                    tx_data = tx_res.get('transaction', {})
                    if 'message' in tx_data:
                        msg = tx_data['message']
                        if 'accountKeys' in msg:
                            raw_keys = msg['accountKeys']
                            if len(raw_keys) > 0:
                                if isinstance(raw_keys[0], str):
                                    keys = raw_keys
                                elif isinstance(raw_keys[0], dict):
                                    keys = [k.get('pubkey') for k in raw_keys]
                                    
                    sender = keys[0] if len(keys) > 0 else "Unknown"
                    receiver = keys[1] if len(keys) > 1 else "Interaction"
                    
                    # Calculate Value
                    pre_bal = meta.get('preBalances', [0])[0] if meta.get('preBalances') else 0
                    post_bal = meta.get('postBalances', [0])[0] if meta.get('postBalances') else 0
                    val = abs(pre_bal - post_bal) / 1e9
                    
                    block_time = tx_res.get('blockTime', int(time.time()))
                    
                    return {
                        'hash': tx_hash,
                        'timestamp': datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S'),
                        'value': val,
                        'from': sender,
                        'to': receiver,
                        'chain': 'solana',
                        'block': tx_res.get('slot', 'Unknown')
                    }
            return None
        except Exception as e:
            print(f"[-] Solana Tx details Error: {e}")
            return None


# ==================== TRON (TronGrid / TronScan) ====================

class TronFetcher:
    """Fetch Tron transactions via TronGrid (Official) or TronScan (Public Fallback)"""
    
    GRID_BASE_URL = "https://api.trongrid.io"
    SCAN_BASE_URL = "https://apilist.tronscan.org/api/transaction"
    
    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        
        # 1. Try TronGrid (Needs Key)
        try:
            print(f"[+] [TronGrid] Fetching transactions for {address[:8]}...")
            headers = {"TRON-PRO-API-KEY": TRON_API_KEY}
            url = f"{TronFetcher.GRID_BASE_URL}/v1/accounts/{address}/transactions"
            params = {'limit': 200}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    for tx in data['data']:
                        # Parse TronGrid Data
                        raw_data = tx.get('raw_data', {}).get('contract', [])[0]
                        params = raw_data.get('parameter', {}).get('value', {})
                        
                        amount = float(params.get('amount', 0)) / 1e6 # Sun to TRX
                        timestamp = tx.get('block_timestamp', 0) / 1000
                        
                        transactions.append({
                            'hash': tx.get('txID'),
                            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            'value': amount,
                            'from': params.get('owner_address'), # Usually hex
                            'to': params.get('to_address'),
                            'chain': 'tron',
                            'type': raw_data.get('type')
                        })
                        
                    counts['normal'] = len(transactions)
                    print(f"[+] Tron (TronGrid): {counts['normal']} transactions")
                    return transactions, counts
            
            print(f"[!] TronGrid Failed ({response.status_code}). Trying TronScan fallback...")
            
        except Exception as e:
            print(f"[!] TronGrid Error: {e}")

        # 2. Try TronScan (Public API)
        try:
            print(f"[+] [TronScan] Fetching transactions for {address[:8]}...")
            
            # Pagination Logic
            start = 0
            limit = 50
            total_fetched = 0
            MAX_FETCH = 500000 # Safety limit
            has_more = True
            
            while has_more and total_fetched < MAX_FETCH:
                params = {
                    'sort': '-timestamp',
                    'count': 'true',
                    'limit': str(limit),
                    'start': str(start),
                    'address': address
                }
                
                # Rate limit protection
                if start > 0: time.sleep(0.5)
                
                response = requests.get(TronFetcher.SCAN_BASE_URL, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    tx_list = data.get('data', [])
                    
                    if not tx_list:
                        has_more = False
                        break
                        
                    for tx in tx_list:
                        # Parse TronScan Data
                        amount = float(tx.get('amount', 0)) / 1e6 # Sun to TRX
                        timestamp = tx.get('timestamp', 0) / 1000
                        
                        transactions.append({
                            'hash': tx.get('hash'),
                            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            'value': amount,
                            'from': tx.get('ownerAddress'),
                            'to': tx.get('toAddress'),
                            'chain': 'tron',
                            'type': 'Transfer'
                        })
                    
                    fetched_count = len(tx_list)
                    total_fetched += fetched_count
                    start += fetched_count
                    print(f"    - Batch: {fetched_count} txs (Total: {len(transactions)})")
                    
                    # Stop if we got fewer than limit (end of list)
                    if fetched_count < limit:
                        has_more = False
                        
                else:
                    print(f"[-] TronScan Error: {response.status_code}")
                    has_more = False # Stop on error
                    
            counts['normal'] = len(transactions)
            print(f"[+] Tron (TronScan): {counts['normal']} transactions")
            return transactions, counts
                
        except Exception as e:
            print(f"[-] TronScan Exception: {e}")
            return [], counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        """Fetch single transaction by hash via TronScan"""
        try:
            url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={tx_hash}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                tx = response.json()
                if tx and tx.get('hash'):
                    # Tron data is complex, pull basic info wrapper
                    amount = 0
                    if 'contractData' in tx and 'amount' in tx['contractData']:
                        amount = float(tx['contractData']['amount']) / 1e6 # Sun to TRX
                    elif 'trigger_info' in tx and 'parameter' in tx['trigger_info'] and '_value' in tx['trigger_info']['parameter']:
                         amount = float(tx['trigger_info']['parameter']['_value']) / 1e6
                         
                    return {
                        'hash': tx.get('hash'),
                        'timestamp': datetime.fromtimestamp(tx.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'value': amount,
                        'from': tx.get('ownerAddress', ''),
                        'to': tx.get('toAddress', ''),
                        'chain': 'tron',
                        'block': tx.get('block', '')
                    }
            return None
        except Exception as e:
            print(f"[-] Tron Tx details Error: {e}")
            return None


# ==================== XRP LEDGER ====================

class XRPLFetcher:
    """Fetch XRP transactions via XRPL public nodes"""
    
    NODES = [
        'https://xrplcluster.com',
        'https://s1.ripple.com:51234',
    ]
    
    @staticmethod
    def fetch_transactions(address: str, limit: int = 200) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        
        for node_url in XRPLFetcher.NODES:
            try:
                payload = {
                    "method": "account_tx",
                    "params": [{
                        "account": address,
                        "limit": limit
                    }]
                }
                
                response = requests.post(node_url, json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data and 'transactions' in data['result']:
                        for item in data['result']['transactions']:
                            tx = item.get('tx', {})
                            transactions.append({
                                'hash': tx.get('hash'),
                                'timestamp': datetime.fromtimestamp(946684800 + tx.get('date', 0)).strftime('%Y-%m-%d %H:%M:%S'), # Ripple Epoch
                                'value': float(tx.get('Amount', 0)) / 1e6 if isinstance(tx.get('Amount'), str) else 0,
                                'from': tx.get('Account'),
                                'to': tx.get('Destination'),
                                'chain': 'xrp'
                            })
                        counts['normal'] = len(transactions)
                        print(f"[+] XRP: {counts['normal']} transactions")
                        return transactions, counts
            except:
                continue
                
        return [], counts


# ==================== UNIFIED INTERFACE ====================

class MultiChainFetcher:
    """Unified interface for all blockchain chains"""
    
    @staticmethod
    def fetch_by_chain(chain: str, address: str, **kwargs) -> Tuple[List[Dict], Dict]:
        """Universal fetch method for any chain with DB persistence check"""
        from modules.core.db_models import SessionLocal, Address, Transaction, Case
        from datetime import datetime
        import pytz
        
        chain = chain.lower()
        
        # 1. Try DB first unless force_refresh is passed
        force_refresh = kwargs.pop('force_refresh', False)
        # Note: We need case_id to fully utilize the DB, but this function is often called globally.
        # We will attempt to find recent analysis for this address across ANY active case for caching purposes,
        # or rely on the caller to handle persistence if they don't pass active_case_id.
        
        db = SessionLocal()
        txs = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        # We don't have active_case_id here easily without passing it down.
        # For this scoped function, we just do the external fetch. The persistence 
        # is handled in app.py's investigation route explicitly.
        # If we wanted full caching here, we'd need to change the function signature
        # to accept a case_id. Since app.py handles the DB lookup BEFORE calling this,
        # we can just keep this as the pure external fetcher, OR we can implement 
        # global address caching here.
        # Given the instruction was to wrap fetch_by_chain, let's implement global caching.
        
        if not force_refresh:
            # Check for recent global address fetch
            addr_record = db.query(Address).filter(Address.address == address).order_by(Address.last_analyzed.desc()).first()
            if addr_record and addr_record.last_analyzed:
                time_since_last = (datetime.utcnow() - addr_record.last_analyzed).total_seconds()
                
                # Load ALL cached txs
                db_txs = db.query(Transaction).filter(
                    (Transaction.from_address == address) | (Transaction.to_address == address)
                ).order_by(Transaction.timestamp.desc()).all()
                
                if db_txs:
                    print(f"[MultiChainFetcher] Cache Hit for {address} on {chain} (Found {len(db_txs)} in DB)")
                    max_block = 0
                    for t in db_txs:
                        if t.block_number and t.block_number > max_block:
                            max_block = t.block_number
                            
                        txs.append({
                            'hash': t.tx_hash,
                            'from': t.from_address,
                            'to': t.to_address,
                            'value': t.amount,
                            'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S') if t.timestamp else '',
                            'block': t.block_number,
                            'chain': chain,
                            'type': t.tx_type
                        })
                    counts['normal'] = len(txs)
                    
                    if time_since_last < 3600: # 1 hour cache instead of 24 to keep data fresher
                        db.close()
                        return txs, counts
                    else:
                        print(f"Cache expired (> 1 hour). Initiating incremental background fetch from block {max_block}...")
                        kwargs['startblock'] = max_block

        db.close()
        print(f"[MultiChainFetcher] Cache Miss/Force Refresh/Incremental for {address}. Fetching external.")
        
        # 2. External Fetch
        # EVM Chains
        evm_aliases = {
            'eth': 'ethereum', 'matic': 'polygon', 'arb': 'arbitrum', 'op': 'optimism', 'binance': 'bsc', 'bnb': 'bsc'
        }
        actual_evm_chain = evm_aliases.get(chain, chain)
        
        if actual_evm_chain in EtherscanMultiChainFetcher.CHAIN_CONFIGS:
            return EtherscanMultiChainFetcher.fetch_transactions(actual_evm_chain, address, **kwargs)
            
        elif actual_evm_chain in BlockScoutFetcher.BLOCKSCOUT_URLS:
            return BlockScoutFetcher.fetch_transactions(actual_evm_chain, address)
        
        # Alchemy EVM Layers
        elif chain in AlchemyEVMFetcher.ALCHEMY_URLS:
            return AlchemyEVMFetcher.fetch_transactions(chain, address)
            
        # Non-EVM Chains (Real Implementations)
        elif chain in ['aptos', 'aptos_testnet']:
            return AlchemyAptosFetcher.fetch_transactions(chain, address)
        elif chain in ['bitcoin', 'btc']:
            return MempoolFetcher.fetch_transactions(address)
        elif chain in ['solana', 'sol']:
            return SolanaFetcher.fetch_transactions(address)
        elif chain in ['tron', 'trx']:
            return TronFetcher.fetch_transactions(address)
        elif chain in ['xrp', 'ripple']:
            return XRPLFetcher.fetch_transactions(address)
        elif chain in ['dogecoin', 'doge']:
            # Use BlockCypher with Pagination (Free Tier friendly)
            return BlockCypherFetcher.fetch_transactions(address)
        
        # === P1 Chains ===
        # LTC, BCH → Trezor public Blockbook (full history)
        elif chain in ['litecoin', 'ltc', 'bitcoin_cash', 'bch',
                       'zcash', 'zec', 'groestlcoin', 'grs', 'peercoin', 'ppc']:
            return BlockbookFetcher.fetch_transactions(chain, address)
        # DASH → BlockCypher (confirmed working)
        elif chain in ['dash']:
            return UTXOBlockCypherFetcher.fetch_transactions(chain, address)
        # DGB → DigiExplorer Insight API
        elif chain in ['digibyte', 'dgb']:
            return InsightFetcher.fetch_transactions('digibyte', address)
        elif chain in ['ecash', 'xec']:
            return ChronIKFetcher.fetch_transactions(address)
        elif chain in ['stellar', 'xlm']:
            return StellarFetcher.fetch_transactions(address)
        elif chain in ['ton']:
            return TONFetcher.fetch_transactions(address)
        elif chain in ['stacks', 'stx']:
            return StacksFetcher.fetch_transactions(address)
        elif chain in ['monero', 'xmr']:
            return MoneroFetcher.fetch_transactions(address)
        # === Moralis: Fantom + supported EVM chains not in Etherscan/Alchemy ===
        elif chain in MoralisFetcher.CHAIN_MAP:
            return MoralisFetcher.fetch_transactions(chain, address)
        else:
            print(f"[!] Unsupported chain '{chain}', defaulting to empty")
            return [], {}
            
    @staticmethod
    def fetch_tx_by_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        """Universal fetch method for a single transaction hash"""
        chain = chain.lower()
        
        # EVM Chains
        evm_aliases = {
            'eth': 'ethereum', 'matic': 'polygon', 'arb': 'arbitrum', 'op': 'optimism', 'binance': 'bsc', 'bnb': 'bsc'
        }
        actual_evm_chain = evm_aliases.get(chain, chain)
        
        if actual_evm_chain in EtherscanMultiChainFetcher.CHAIN_CONFIGS:
            return EtherscanMultiChainFetcher.fetch_by_tx_hash(actual_evm_chain, tx_hash)
            
        elif actual_evm_chain in BlockScoutFetcher.BLOCKSCOUT_URLS:
            return BlockScoutFetcher.fetch_by_tx_hash(actual_evm_chain, tx_hash)
            
        elif chain in AlchemyEVMFetcher.ALCHEMY_URLS:
            return AlchemyEVMFetcher.fetch_by_tx_hash(chain, tx_hash)
            
        # Non-EVM Chains
        elif chain in ['aptos', 'aptos_testnet']:
            return AlchemyAptosFetcher.fetch_by_tx_hash(chain, tx_hash)
        elif chain in ['bitcoin', 'btc']:
            return MempoolFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['solana', 'sol']:
            return SolanaFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['tron', 'trx']:
            return TronFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['dogecoin', 'doge']:
            return BlockCypherFetcher.fetch_by_tx_hash(tx_hash)
        
        # === P1 Chains TX Hash Lookup ===
        elif chain in ['litecoin', 'ltc', 'bitcoin_cash', 'bch',
                       'zcash', 'zec', 'groestlcoin', 'grs', 'peercoin', 'ppc']:
            return BlockbookFetcher.fetch_by_tx_hash(chain, tx_hash)
        elif chain in ['dash']:
            return UTXOBlockCypherFetcher.fetch_by_tx_hash(chain, tx_hash)
        elif chain in ['digibyte', 'dgb']:
            return InsightFetcher.fetch_by_tx_hash('digibyte', tx_hash)
        elif chain in ['ecash', 'xec']:
            return ChronIKFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['stellar', 'xlm']:
            return StellarFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['ton']:
            return TONFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['stacks', 'stx']:
            return StacksFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['monero', 'xmr']:
            return MoneroFetcher.fetch_by_tx_hash(tx_hash)
        
        else:
            print(f"[!] Unsupported chain '{chain}' for hash lookup")
            return None
    
    @staticmethod
    def get_explorer_url(chain: str, address: str) -> str:
        explorers = {
            'ethereum': f'https://etherscan.io/address/{address}',
            'polygon': f'https://polygonscan.com/address/{address}',
            'bitcoin': f'https://mempool.space/address/{address}',
            'solana': f'https://solscan.io/account/{address}',
            'tron': f'https://tronscan.org/#/address/{address}',
            'xrp': f'https://xrpscan.com/account/{address}',
            'dogecoin': f'https://dogechain.info/address/{address}',
            'gnosis': f'https://gnosisscan.io/address/{address}',
            'celo': f'https://celoscan.io/address/{address}',
            'blast': f'https://blastscan.io/address/{address}',
            'linea': f'https://lineascan.build/address/{address}',
            'polygon_zkevm': f'https://zkevm.polygonscan.com/address/{address}',
            'mantle': f'https://explorer.mantle.xyz/address/{address}',
            'bob': f'https://explorer.gobob.xyz/address/{address}',
            'botanix': f'https://blockscout.botanixlabs.dev/address/{address}',
            'galactica': f'https://explorer.galactica.com/address/{address}',
            'opbnb': f'https://opbnbscan.com/address/{address}',
            'sei': f'https://seitrace.com/address/{address}',
            'zksync': f'https://explorer.zksync.io/address/{address}',
            'scroll': f'https://scrollscan.com/address/{address}',
            'rootstock': f'https://explorer.rootstock.io/address/{address}',
            'aptos': f'https://explorer.aptoslabs.com/account/{address}'
        }
        return explorers.get(chain, '#')

    @staticmethod
    def get_tx_explorer_url(chain: str) -> str:
        explorers = {
            'ethereum': 'https://etherscan.io/tx/',
            'bsc': 'https://bscscan.com/tx/',
            'polygon': 'https://polygonscan.com/tx/',
            'arbitrum': 'https://arbiscan.io/tx/',
            'optimism': 'https://optimistic.etherscan.io/tx/',
            'base': 'https://basescan.org/tx/',
            'avalanche': 'https://snowtrace.io/tx/',
            'bitcoin': 'https://mempool.space/tx/',
            'solana': 'https://solscan.io/tx/',
            'tron': 'https://tronscan.org/#/transaction/',
            'xrp': 'https://xrpscan.com/tx/',
            'dogecoin': 'https://dogechain.info/tx/',
            'gnosis': 'https://gnosisscan.io/tx/',
            'celo': 'https://celoscan.io/tx/',
            'blast': 'https://blastscan.io/tx/',
            'linea': 'https://lineascan.build/tx/',
            'polygon_zkevm': 'https://zkevm.polygonscan.com/tx/',
            'mantle': 'https://explorer.mantle.xyz/tx/',
            'bob': 'https://explorer.gobob.xyz/tx/',
            'botanix': 'https://blockscout.botanixlabs.dev/tx/',
            'galactica': 'https://explorer.galactica.com/tx/',
            'opbnb': 'https://opbnbscan.com/tx/',
            'sei': 'https://seitrace.com/tx/',
            'zksync': 'https://explorer.zksync.io/tx/',
            'scroll': 'https://scrollscan.com/tx/',
            'rootstock': 'https://explorer.rootstock.io/tx/',
            'aptos': 'https://explorer.aptoslabs.com/txn/'
        }
        # Fallback to etherscan
        return explorers.get(chain, 'https://etherscan.io/tx/')

if __name__ == '__main__':
    print("Test run...")

# ==================== MORALIS FETCHER (Fantom + 20 EVM chains) ====================

class MoralisFetcher:
    """Fetch EVM transactions via Moralis Deep Index API.
    Free tier: 40,000 requests/day.
    Covers: Fantom, BNB, Avalanche, Cronos, Arbitrum, Optimism, Base, Polygon, Linea, and more."""

    BASE = 'https://deep-index.moralis.io/api/v2.2'

    # Moralis chain slug mapping
    CHAIN_MAP = {
        'fantom': 'fantom',
        'ftm': 'fantom',
        'bnb': 'bsc',
        'bsc': 'bsc',
        'avalanche': 'avalanche',
        'avax': 'avalanche',
        'cronos': 'cronos',
        'cro': 'cronos',
        'arbitrum': 'arbitrum',
        'optimism': 'optimism',
        'base': 'base',
        'polygon': 'polygon',
        'matic': 'polygon',
        'linea': 'linea',
        'moonbeam': 'moonbeam',
        'moonriver': 'moonriver',
        'gnosis': 'gnosis',
        'celo': 'celo',
        'ethereum': 'eth',
        'eth': 'eth',
    }

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        moralis_chain = MoralisFetcher.CHAIN_MAP.get(chain.lower())
        if not moralis_chain or not MORALIS_API_KEY:
            return [], {'normal': 0}

        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        headers = {'X-API-Key': MORALIS_API_KEY, 'accept': 'application/json'}

        try:
            print(f"[+] Moralis: Fetching {chain} ({moralis_chain}) transactions for {address[:12]}...")
            cursor = None
            page_count = 0

            while True:
                params = {
                    'chain': moralis_chain,
                    'limit': 100,
                    'order': 'DESC',
                }
                if cursor:
                    params['cursor'] = cursor

                resp = requests.get(
                    f"{MoralisFetcher.BASE}/wallets/{address}/history",
                    headers=headers, params=params, timeout=20
                )

                if resp.status_code == 401:
                    print(f"[-] Moralis: Auth error — check API key")
                    break
                if resp.status_code != 200:
                    print(f"[-] Moralis HTTP {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                results = data.get('result', [])

                if not results:
                    break

                for tx in results:
                    from_addr = safe_checksum(tx.get('from_address', 'Unknown'))
                    to_addr = safe_checksum(tx.get('to_address') or tx.get('receipt_contract_address') or 'Unknown')
                    value_wei = int(tx.get('value', 0) or 0)
                    value = value_wei / 1e18

                    # Determine type
                    tx_type = 'normal'
                    if tx.get('category') in ('erc20', 'token'):
                        tx_type = 'erc20'
                        counts['token'] += 1
                    elif tx.get('category') == 'internal':
                        tx_type = 'internal'
                        counts['internal'] += 1
                    else:
                        counts['normal'] += 1

                    block_ts = tx.get('block_timestamp', '')
                    try:
                        if block_ts:
                            # Moralis returns ISO8601 format
                            block_ts = block_ts.replace('T', ' ').split('.')[0].replace('Z', '')
                    except:
                        pass

                    transactions.append({
                        'hash': tx.get('hash', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': block_ts,
                        'block': tx.get('block_number', 0),
                        'chain': chain,
                        'type': tx_type,
                        'asset': tx.get('native_token_symbol', '')
                    })

                cursor = data.get('cursor')
                page_count += 1
                if not cursor:
                    break
                time.sleep(0.15)  # Respect free tier (40K req/day)

            total = sum(counts.values())
            print(f"[+] {chain} (Moralis): {total} transactions across {page_count} pages")

        except Exception as e:
            print(f"[-] Moralis {chain} error: {e}")

        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        moralis_chain = MoralisFetcher.CHAIN_MAP.get(chain.lower())
        if not moralis_chain or not MORALIS_API_KEY:
            return None
        headers = {'X-API-Key': MORALIS_API_KEY, 'accept': 'application/json'}
        try:
            resp = requests.get(
                f"{MoralisFetcher.BASE}/transaction/{tx_hash}",
                headers=headers, params={'chain': moralis_chain}, timeout=15
            )
            if resp.status_code == 200:
                tx = resp.json()
                block_ts = tx.get('block_timestamp', '').replace('T', ' ').split('.')[0].replace('Z', '')
                return {
                    'hash': tx_hash,
                    'from': safe_checksum(tx.get('from_address', 'Unknown')),
                    'to': safe_checksum(tx.get('to_address') or 'Unknown'),
                    'value': int(tx.get('value', 0) or 0) / 1e18,
                    'timestamp': block_ts,
                    'block': tx.get('block_number', 0),
                    'chain': chain
                }
        except Exception as e:
            print(f"[-] Moralis TX hash error: {e}")
        return None


# ==================== COVALENT / GOLDRUSH FETCHER (Universal EVM fallback — 200+ chains) ====================

class CovalentFetcher:
    """Universal EVM fallback via Covalent GoldRush API.
    Free tier: 100K requests/month.
    Covers 200+ chains by numeric chain_id as universal fallback."""

    BASE = 'https://api.covalenthq.com/v1'

    # Chain ID mapping for Covalent
    CHAIN_IDS = {
        'ethereum': 1, 'eth': 1,
        'polygon': 137, 'matic': 137,
        'bnb': 56, 'bsc': 56,
        'avalanche': 43114, 'avax': 43114,
        'fantom': 250, 'ftm': 250,
        'arbitrum': 42161,
        'optimism': 10,
        'base': 8453,
        'gnosis': 100,
        'celo': 42220,
        'moonbeam': 1284,
        'moonriver': 1285,
        'cronos': 25,
        'linea': 59144,
        'scroll': 534352,
        'zksync': 324,
        'polygon_zkevm': 1101,
        'mantle': 5000,
        'blast': 81457,
        'taiko': 167000,
        'metis': 1088,
        'kava': 2222,
        'aurora': 1313161554,
        'harmony': 1666600000,
    }

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        chain_id = CovalentFetcher.CHAIN_IDS.get(chain.lower())
        if not chain_id or not COVALENT_API_KEY:
            return [], {'normal': 0}

        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] Covalent: Fetching {chain} (chain_id={chain_id}) for {address[:12]}...")
            page = 0
            page_size = 100

            while True:
                url = f"{CovalentFetcher.BASE}/{chain_id}/address/{address}/transactions_v3/"
                params = {'page-size': page_size, 'page-number': page}
                resp = requests.get(url, params=params, auth=(COVALENT_API_KEY, ''), timeout=20)

                if resp.status_code != 200:
                    print(f"[-] Covalent HTTP {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json().get('data', {})
                items = data.get('items', [])
                if not items:
                    break

                for tx in items:
                    from_addr = safe_checksum(tx.get('from_address', 'Unknown'))
                    to_addr = safe_checksum(tx.get('to_address') or 'Unknown')
                    value = int(tx.get('value', 0) or 0) / 1e18
                    ts = tx.get('block_signed_at', '')
                    if ts:
                        ts = ts.replace('T', ' ').split('.')[0].replace('Z', '')

                    transactions.append({
                        'hash': tx.get('tx_hash', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': ts,
                        'block': tx.get('block_height', 0),
                        'chain': chain,
                        'type': 'normal'
                    })
                    counts['normal'] += 1

                pagination = data.get('pagination', {})
                has_more = pagination.get('has_more', False)
                if not has_more or len(items) < page_size:
                    break
                page += 1
                time.sleep(0.2)

            print(f"[+] {chain} (Covalent): {counts['normal']} transactions")

        except Exception as e:
            print(f"[-] Covalent {chain} error: {e}")

        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        chain_id = CovalentFetcher.CHAIN_IDS.get(chain.lower())
        if not chain_id or not COVALENT_API_KEY:
            return None
        try:
            url = f"{CovalentFetcher.BASE}/{chain_id}/transaction_v2/{tx_hash}/"
            resp = requests.get(url, auth=(COVALENT_API_KEY, ''), timeout=15)
            if resp.status_code == 200:
                items = resp.json().get('data', {}).get('items', [])
                if items:
                    tx = items[0]
                    ts = tx.get('block_signed_at', '').replace('T', ' ').split('.')[0].replace('Z', '')
                    return {
                        'hash': tx_hash,
                        'from': safe_checksum(tx.get('from_address', 'Unknown')),
                        'to': safe_checksum(tx.get('to_address') or 'Unknown'),
                        'value': int(tx.get('value', 0) or 0) / 1e18,
                        'timestamp': ts,
                        'block': tx.get('block_height', 0),
                        'chain': chain
                    }
        except Exception as e:
            print(f"[-] Covalent TX hash error: {e}")
        return None


# ==================== P1 CHAINS: UTXO CHAINS (No Blockchair) ====================

TON_API_KEY = os.getenv('TON_API_KEY', '')

# BlockCypher already covers DOGE — extend it to BCH, LTC, DASH
# These chain slugs are the BlockCypher v1 API path segments
BLOCKCYPHER_P1_CHAINS = {
    'bitcoin_cash': 'bch/main',
    'bch': 'bch/main',
    'litecoin': 'ltc/main',
    'ltc': 'ltc/main',
    'dash': 'dash/main',
}

class UTXOBlockCypherFetcher:
    """Fetch BCH, LTC, DASH transactions via BlockCypher (existing key).
    Uses the same BlockCypher token already in .env for Dogecoin."""

    BASE = 'https://api.blockcypher.com/v1'
    TOKEN = os.getenv('BLOCKCYPHER_TOKEN', '280c03c6f8f34afb9d6f5e1b1fb1ab59')

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        slug = BLOCKCYPHER_P1_CHAINS.get(chain.lower())
        if not slug:
            return [], {'normal': 0}

        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] BlockCypher P1: Fetching {chain} transactions for {address[:12]}...")
            before_bh = None

            while True:
                url = f"{UTXOBlockCypherFetcher.BASE}/{slug}/addrs/{address}/full"
                params = {
                    'token': UTXOBlockCypherFetcher.TOKEN,
                    'limit': 200,
                    'includeHex': False
                }
                if before_bh:
                    params['before'] = before_bh

                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    print(f"[-] BlockCypher P1 HTTP {resp.status_code} for {chain}")
                    break

                data = resp.json()
                txs = data.get('txs', [])
                if not txs:
                    break

                for tx in txs:
                    inputs = tx.get('inputs', [])
                    outputs = tx.get('outputs', [])
                    from_addr = (inputs[0].get('addresses') or ['Unknown'])[0] if inputs else 'Unknown'
                    to_addr = (outputs[0].get('addresses') or ['Unknown'])[0] if outputs else 'Unknown'
                    value = tx.get('total', 0) / 1e8

                    transactions.append({
                        'hash': tx.get('hash', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': tx.get('received', ''),
                        'block': tx.get('block_height', 0),
                        'chain': chain,
                        'type': 'normal'
                    })
                    before_bh = tx.get('block_height', before_bh)

                if len(txs) < 200:
                    break
                time.sleep(0.3)

            counts['normal'] = len(transactions)
            print(f"[+] {chain} (BlockCypher): {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] BlockCypher P1 {chain} error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        slug = BLOCKCYPHER_P1_CHAINS.get(chain.lower())
        if not slug:
            return None
        try:
            url = f"{UTXOBlockCypherFetcher.BASE}/{slug}/txs/{tx_hash}"
            resp = requests.get(url, params={'token': UTXOBlockCypherFetcher.TOKEN}, timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                inputs = tx.get('inputs', [])
                outputs = tx.get('outputs', [])
                return {
                    'hash': tx_hash,
                    'from': (inputs[0].get('addresses') or ['Unknown'])[0] if inputs else 'Unknown',
                    'to': (outputs[0].get('addresses') or ['Unknown'])[0] if outputs else 'Unknown',
                    'value': tx.get('total', 0) / 1e8,
                    'timestamp': tx.get('received', ''),
                    'block': tx.get('block_height', 0),
                    'chain': chain
                }
        except Exception as e:
            print(f"[-] BlockCypher P1 TX error: {e}")
        return None


# ==================== P1 CHAINS: INSIGHT API (DGB, DASH) ====================

class InsightFetcher:
    """Fetch transactions via Bitcore/Insight REST API (BitPay open-source).
    No API key required. Covers DigiByte (digiexplorer.info) and DASH (insight.dash.org)."""

    ENDPOINTS = {
        'digibyte': 'https://digiexplorer.info/insight-api',
        'dgb': 'https://digiexplorer.info/insight-api',
        'dash': 'http://insight.dash.org/insight-api',
    }

    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        base = InsightFetcher.ENDPOINTS.get(chain.lower())
        if not base:
            return [], {'normal': 0}

        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] Insight ({chain}): Fetching transactions for {address[:12]}...")
            from_idx = 0
            page_size = 50

            while True:
                url = f"{base}/addrs/{address}/txs"
                params = {'from': from_idx, 'to': from_idx + page_size}
                resp = requests.get(url, params=params, timeout=20)

                if resp.status_code != 200:
                    print(f"[-] Insight HTTP {resp.status_code} for {chain}")
                    break

                data = resp.json()
                items = data.get('items', [])
                if not items:
                    break

                for tx in items:
                    vin = tx.get('vin', [])
                    vout = tx.get('vout', [])
                    from_addr = vin[0].get('addr', 'Unknown') if vin else 'Unknown'
                    to_addr = vout[0].get('scriptPubKey', {}).get('addresses', ['Unknown'])[0] if vout else 'Unknown'
                    value = float(tx.get('valueOut', 0) or 0)
                    ts_raw = tx.get('time', 0) or tx.get('blocktime', 0)
                    ts = datetime.utcfromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S') if ts_raw else ''

                    transactions.append({
                        'hash': tx.get('txid', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': ts,
                        'block': tx.get('blockheight', 0),
                        'chain': chain,
                        'type': 'normal'
                    })

                total_items = data.get('totalItems', len(items))
                from_idx += page_size
                if from_idx >= total_items:
                    break
                time.sleep(0.2)

            counts['normal'] = len(transactions)
            print(f"[+] {chain} (Insight): {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] Insight {chain} error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        base = InsightFetcher.ENDPOINTS.get(chain.lower())
        if not base:
            return None
        try:
            resp = requests.get(f"{base}/tx/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                vin = tx.get('vin', [])
                vout = tx.get('vout', [])
                ts_raw = tx.get('time', 0) or tx.get('blocktime', 0)
                return {
                    'hash': tx_hash,
                    'from': vin[0].get('addr', 'Unknown') if vin else 'Unknown',
                    'to': vout[0].get('scriptPubKey', {}).get('addresses', ['Unknown'])[0] if vout else 'Unknown',
                    'value': float(tx.get('valueOut', 0) or 0),
                    'timestamp': datetime.utcfromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S') if ts_raw else '',
                    'block': tx.get('blockheight', 0),
                    'chain': chain
                }
        except Exception as e:
            print(f"[-] Insight TX hash error: {e}")
        return None


# ==================== P1 CHAINS: ECASH (XEC) via ChronIK ====================

class ChronIKFetcher:
    """Fetch eCash (XEC) transactions via the official ChronIK indexer.
    ChronIK is built directly into the eCash node — 100% free, no key."""

    # Primary: official eCash Foundation Chronik; fallback: be.cash mirror
    BASE = 'https://chronik.e.cash'
    BASE_FALLBACK = 'https://chronik.be.cash/xec'

    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] ChronIK (eCash): Fetching transactions for {address[:12]}...")
            page = 0
            page_size = 200

            while True:
                # ChronIK REST API: /blockchain/address/{addr}/transactions
                url = f"{ChronIKFetcher.BASE}/blockchain/address/{address}/transactions"
                params = {'page': page, 'pageSize': page_size}
                resp = requests.get(url, params=params, timeout=25)
                if resp.status_code != 200:
                    # Fallback to be.cash mirror with different URL format
                    url2 = f"{ChronIKFetcher.BASE_FALLBACK}/address/{address}/txs"
                    resp = requests.get(url2, timeout=25)
                    if resp.status_code != 200:
                        break

                data = resp.json()
                txs = data.get('txs', [])
                if not txs:
                    break

                for tx in txs:
                    inputs = tx.get('inputs', [])
                    outputs = tx.get('outputs', [])
                    from_addr = inputs[0].get('outputScript', 'Unknown') if inputs else 'Unknown'
                    to_addr = outputs[0].get('outputScript', 'Unknown') if outputs else 'Unknown'
                    value = sum(int(o.get('value', 0)) for o in outputs) / 1e2  # satoshi to XEC (1 XEC = 100 sats)

                    transactions.append({
                        'hash': tx.get('txid', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': datetime.utcfromtimestamp(tx.get('timeFirstSeen', 0) or tx.get('block', {}).get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'block': tx.get('block', {}).get('height', 0),
                        'chain': 'ecash',
                        'type': 'normal'
                    })

                num_pages = data.get('numPages', 1)
                if page + 1 >= num_pages:
                    break
                page += 1
                time.sleep(0.2)

            counts['normal'] = len(transactions)
            print(f"[+] eCash (ChronIK): {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] ChronIK eCash error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        try:
            resp = requests.get(f"{ChronIKFetcher.BASE}/tx/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                inputs = tx.get('inputs', [])
                outputs = tx.get('outputs', [])
                return {
                    'hash': tx_hash,
                    'from': inputs[0].get('outputScript', 'Unknown') if inputs else 'Unknown',
                    'to': outputs[0].get('outputScript', 'Unknown') if outputs else 'Unknown',
                    'value': sum(int(o.get('value', 0)) for o in outputs) / 1e2,
                    'timestamp': datetime.utcfromtimestamp(tx.get('timeFirstSeen', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'block': tx.get('block', {}).get('height', 0),
                    'chain': 'ecash'
                }
        except Exception as e:
            print(f"[-] ChronIK TX error: {e}")
        return None


# ==================== P1 CHAINS: BLOCKBOOK (Groestlcoin, Peercoin, DigiByte, Zcash) ====================

class BlockbookFetcher:
    """Fetch transactions via public Blockbook APIs (Trezor open-source explorer).
    GRS/PPC use chain-specific nodes; DGB and ZEC use Trezor public nodes."""

    ENDPOINTS = {
        'groestlcoin': 'https://blockbook.groestlcoin.org',
        'grs': 'https://blockbook.groestlcoin.org',
        'peercoin': 'https://blockbook.peercoin.net',
        'ppc': 'https://blockbook.peercoin.net',
        # Trezor public Blockbook instances — numbered subdomain pattern
        'zcash': 'https://zec1.trezor.io',
        'zec': 'https://zec1.trezor.io',
        # Correct Trezor LTC/BCH subdomains (numbered pattern like zec1)
        'litecoin': 'https://ltc1.trezor.io',
        'ltc': 'https://ltc1.trezor.io',
        'bitcoin_cash': 'https://bch1.trezor.io',
        'bch': 'https://bch1.trezor.io',
    }


    @staticmethod
    def fetch_transactions(chain: str, address: str) -> Tuple[List[Dict], Dict]:
        base = BlockbookFetcher.ENDPOINTS.get(chain.lower())
        if not base:
            return [], {'normal': 0}

        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] Blockbook: Fetching {chain} transactions for {address[:12]}...")
            page = 1
            while True:
                url = f"{base}/api/v2/address/{address}"
                params = {'page': page, 'pageSize': 50, 'details': 'txs'}
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                txs = data.get('transactions') or []
                for tx in txs:
                    vin = tx.get('vin', [])
                    vout = tx.get('vout', [])
                    from_addr = vin[0].get('addresses', ['Unknown'])[0] if vin else 'Unknown'
                    to_addr = vout[0].get('addresses', ['Unknown'])[0] if vout else 'Unknown'
                    value = int(tx.get('value', 0)) / 1e8
                    transactions.append({
                        'hash': tx.get('txid', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': datetime.utcfromtimestamp(tx.get('blockTime', 0)).strftime('%Y-%m-%d %H:%M:%S') if tx.get('blockTime') else '',
                        'block': tx.get('blockHeight', 0),
                        'chain': chain,
                        'type': 'normal'
                    })
                total_pages = data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1
                time.sleep(0.3)
            counts['normal'] = len(transactions)
            print(f"[+] {chain}: {counts['normal']} transactions via Blockbook")
        except Exception as e:
            print(f"[-] Blockbook {chain} error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        base = BlockbookFetcher.ENDPOINTS.get(chain.lower())
        if not base:
            return None
        try:
            resp = requests.get(f"{base}/api/v2/tx/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                vin = tx.get('vin', [])
                vout = tx.get('vout', [])
                return {
                    'hash': tx_hash,
                    'from': vin[0].get('addresses', ['Unknown'])[0] if vin else 'Unknown',
                    'to': vout[0].get('addresses', ['Unknown'])[0] if vout else 'Unknown',
                    'value': int(tx.get('value', 0)) / 1e8,
                    'timestamp': datetime.utcfromtimestamp(tx.get('blockTime', 0)).strftime('%Y-%m-%d %H:%M:%S') if tx.get('blockTime') else '',
                    'block': tx.get('blockHeight', 0),
                    'chain': chain
                }
        except Exception as e:
            print(f"[-] Blockbook TX hash error: {e}")
        return None


# ==================== P1 CHAINS: STELLAR (XLM) ====================

class StellarFetcher:
    """Fetch Stellar transactions via public Horizon API"""

    HORIZON = 'https://horizon.stellar.org'

    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] Stellar Horizon: Fetching transactions for {address[:12]}...")
            url = f"{StellarFetcher.HORIZON}/accounts/{address}/transactions"
            params = {'limit': 200, 'order': 'desc'}

            while True:
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                records = data.get('_embedded', {}).get('records', [])
                for tx in records:
                    transactions.append({
                        'hash': tx.get('hash', ''),
                        'from': tx.get('source_account', 'Unknown'),
                        'to': address,  # Stellar doesn't expose simple to in tx root
                        'value': float(tx.get('fee_charged', 0)) / 1e7,
                        'timestamp': tx.get('created_at', ''),
                        'block': tx.get('ledger', 0),
                        'chain': 'stellar',
                        'type': 'normal'
                    })
                # Pagination
                next_link = data.get('_links', {}).get('next', {}).get('href')
                if not next_link or len(records) < 200:
                    break
                url = next_link
                params = {}
                time.sleep(0.2)

            counts['normal'] = len(transactions)
            print(f"[+] Stellar: {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] Stellar error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        try:
            resp = requests.get(f"{StellarFetcher.HORIZON}/transactions/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                return {
                    'hash': tx_hash,
                    'from': tx.get('source_account', 'Unknown'),
                    'to': 'See operations',
                    'value': float(tx.get('fee_charged', 0)) / 1e7,
                    'timestamp': tx.get('created_at', ''),
                    'block': tx.get('ledger', 0),
                    'chain': 'stellar'
                }
        except Exception as e:
            print(f"[-] Stellar TX hash error: {e}")
        return None


# ==================== P1 CHAINS: TON ====================

class TONFetcher:
    """Fetch TON transactions via TonCenter API"""

    BASE = 'https://toncenter.com/api/v2'

    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] TON TonCenter: Fetching transactions for {address[:12]}...")
            limit = 100
            lt = None
            hash_arg = None

            while True:
                params = {
                    'address': address,
                    'limit': limit,
                    'api_key': TON_API_KEY
                }
                if lt:
                    params['lt'] = lt
                    params['hash'] = hash_arg

                resp = requests.get(f"{TONFetcher.BASE}/getTransactions", params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                if not data.get('ok'):
                    break
                txs = data.get('result', [])
                if not txs:
                    break

                for tx in txs:
                    msg_in = tx.get('in_msg', {}) or {}
                    msg_out = (tx.get('out_msgs') or [{}])[0]
                    from_addr = msg_in.get('source', 'Unknown') or 'Unknown'
                    to_addr = msg_in.get('destination', address) or address
                    value = int(msg_in.get('value', 0)) / 1e9  # nanotons to TON

                    transactions.append({
                        'hash': tx.get('transaction_id', {}).get('hash', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': datetime.utcfromtimestamp(tx.get('utime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'block': tx.get('transaction_id', {}).get('lt', 0),
                        'chain': 'ton',
                        'type': 'normal'
                    })

                if len(txs) < limit:
                    break
                # Paginate using last transaction's lt and hash
                last = txs[-1].get('transaction_id', {})
                lt = last.get('lt')
                hash_arg = last.get('hash')
                time.sleep(0.3)

            counts['normal'] = len(transactions)
            print(f"[+] TON: {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] TON error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        try:
            # TonCenter doesn't support direct TX hash lookup; return partial info
            return {
                'hash': tx_hash,
                'from': 'See TON explorer',
                'to': 'See TON explorer',
                'value': 0.0,
                'timestamp': '',
                'block': 0,
                'chain': 'ton'
            }
        except Exception as e:
            print(f"[-] TON TX hash error: {e}")
        return None


# ==================== P1 CHAINS: STACKS (STX) ====================

class StacksFetcher:
    """Fetch Stacks (STX) transactions via Hiro API (free, no key needed)"""

    BASE = 'https://api.hiro.so'

    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        transactions = []
        counts = {'normal': 0}
        try:
            print(f"[+] Stacks Hiro: Fetching transactions for {address[:12]}...")
            offset = 0
            limit = 50

            while True:
                url = f"{StacksFetcher.BASE}/extended/v1/address/{address}/transactions"
                params = {'limit': limit, 'offset': offset}
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                txs = data.get('results', [])
                if not txs:
                    break

                for tx in txs:
                    from_addr = tx.get('sender_address', 'Unknown')
                    # For contract calls, to is the contract address
                    to_addr = tx.get('token_transfer', {}).get('recipient_address') or tx.get('contract_call', {}).get('contract_id') or address
                    value = int(tx.get('token_transfer', {}).get('amount', 0)) / 1e6  # microSTX to STX

                    transactions.append({
                        'hash': tx.get('tx_id', ''),
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'timestamp': datetime.utcfromtimestamp(tx.get('burn_block_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if tx.get('burn_block_time') else '',
                        'block': tx.get('block_height', 0),
                        'chain': 'stacks',
                        'type': 'normal'
                    })

                total = data.get('total', 0)
                if offset + limit >= total:
                    break
                offset += limit
                time.sleep(0.2)

            counts['normal'] = len(transactions)
            print(f"[+] Stacks: {counts['normal']} transactions")
        except Exception as e:
            print(f"[-] Stacks error: {e}")
        return transactions, counts

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        try:
            resp = requests.get(f"{StacksFetcher.BASE}/extended/v1/tx/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json()
                return {
                    'hash': tx_hash,
                    'from': tx.get('sender_address', 'Unknown'),
                    'to': tx.get('token_transfer', {}).get('recipient_address') or tx.get('contract_call', {}).get('contract_id') or 'Unknown',
                    'value': int(tx.get('token_transfer', {}).get('amount', 0)) / 1e6,
                    'timestamp': datetime.utcfromtimestamp(tx.get('burn_block_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if tx.get('burn_block_time') else '',
                    'block': tx.get('block_height', 0),
                    'chain': 'stacks'
                }
        except Exception as e:
            print(f"[-] Stacks TX hash error: {e}")
        return None


# ==================== P1 CHAINS: MONERO (XMR — TX Hash only) ====================

class MoneroFetcher:
    """Monero TX hash lookup via xmrchain.net. 
    NOTE: Monero is a privacy chain. Address history is NOT publicly available by design."""

    BASE = 'https://xmrchain.net/api'

    @staticmethod
    def fetch_transactions(address: str) -> Tuple[List[Dict], Dict]:
        print("[!] Monero: Address transaction history unavailable — Monero is a privacy chain by design.")
        return [], {'normal': 0}

    @staticmethod
    def fetch_by_tx_hash(tx_hash: str) -> Optional[Dict]:
        try:
            resp = requests.get(f"{MoneroFetcher.BASE}/transaction/{tx_hash}", timeout=15)
            if resp.status_code == 200:
                tx = resp.json().get('data', {})
                return {
                    'hash': tx_hash,
                    'from': 'Hidden (Monero privacy)',
                    'to': 'Hidden (Monero privacy)',
                    'value': float(tx.get('xmr_outputs', 0)),
                    'timestamp': tx.get('timestamp_utc', ''),
                    'block': tx.get('block_no', 0),
                    'chain': 'monero'
                }
        except Exception as e:
            print(f"[-] Monero TX hash error: {e}")
        return None

