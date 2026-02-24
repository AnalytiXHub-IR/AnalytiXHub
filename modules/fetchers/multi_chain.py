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
SOLANA_API_KEY = os.getenv('SOLANA_API_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3NzA3MTg3MzU5ODAsImVtYWlsIjoia29sbHVydXNhaWFiaGlyYW01MTNAZ21haWwuY29tIiwiYWN0aW9uIjoidG9rZW4tYXBpIiwiYXBpVmVyc2lvbiI6InYyIiwiaWF0IjoxNzcwNzE4NzM1fQ.SGdL7FJRYiMhC5YnSky-6UXCa4NLOgkoWSvhD2AvRDg")
HELIUS_API_KEY = os.getenv('HELIUS_API_KEY', "a44ade62-a70f-4b75-8054-3e8388f70058")
TRON_API_KEY = os.getenv('TRON_API_KEY', "72ac1d93-4497-4664-a844-f730b2b5e606")

# ==================== BLOCKSCOUT (Free EVM API) ====================

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
        chain = chain.lower()
        if chain not in BlockScoutFetcher.BLOCKSCOUT_URLS:
            return [], {'normal': 0, 'internal': 0, 'token': 0}
        
        base_url = BlockScoutFetcher.BLOCKSCOUT_URLS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        try:
            tx_url = f"{base_url}/addresses/{address}/transactions"
            tx_response = requests.get(tx_url, timeout=15)
            
            if tx_response.status_code == 200:
                tx_data = tx_response.json()
                if 'items' in tx_data:
                    for tx in tx_data['items']: # Process all returned items
                        transactions.append({
                            'hash': tx.get('hash'),
                            'from': tx.get('from', {}).get('hash') if isinstance(tx.get('from'), dict) else tx.get('from'),
                            'to': tx.get('to', {}).get('hash') if isinstance(tx.get('to'), dict) else tx.get('to'),
                            'value': float(tx.get('value', 0)) if tx.get('value') else 0,
                            'timestamp': tx.get('timestamp') or datetime.now().isoformat(),
                            'block': tx.get('block', 0),
                            'chain': chain
                        })
                counts['normal'] = len(transactions)
                print(f"✅ {chain.upper()} (BlockScout): {counts['normal']} transactions")
            
            return transactions, counts
        
        except Exception as e:
            print(f"❌ BlockScout {chain} error: {e}")
            return [], counts

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
                        'from': tx.get('from', {}).get('hash') if isinstance(tx.get('from'), dict) else tx.get('from'),
                        'to': tx.get('to', {}).get('hash') if isinstance(tx.get('to'), dict) else tx.get('to'),
                        'value': float(tx.get('value', 0)) / 1e18 if tx.get('value') else 0.0,
                        'timestamp': tx.get('timestamp') or datetime.now().isoformat(),
                        'block': tx.get('block', 0),
                        'chain': chain
                    }
            return None
        except Exception as e:
            print(f"❌ BlockScout Tx details Error: {e}")
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
            MAX_FETCH = 5000 # Capture everything for the user's "1600-1700 txs" case
            
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
                            print(f"⚠️ BlockCypher Rate Limit (429). Waiting {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue # Retry
                        
                        if response.status_code == 200:
                            break # Success
                        else:
                            print(f"❌ BlockCypher Error: {response.status_code} - {response.text[:100]}")
                            response = None
                            break # Don't retry other errors immediately
                            
                    except requests.exceptions.Timeout:
                        print(f"⚠️ Timeout. Retrying...")
                    except Exception as e:
                        print(f"⚠️ Network Error: {e}")
                        time.sleep(5)
                
                # If failed after all retries, break pagination loop
                if not response or response.status_code != 200:
                    print("❌ Failed to fetch BlockCypher batch after retries.")
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
            print(f"✅ Dogecoin (BlockCypher): {counts['normal']} transactions (Paginated)")
                
            # Fallback to GetBlock.io if BlockCypher failed totally
            if len(transactions) == 0:
                 return MempoolFetcher._fetch_via_getblock(address)
                 
            return transactions, counts
            
        except Exception as e:
            print(f"❌ Dogecoin fetch error: {e}")
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
            print(f"❌ BlockCypher Tx details Error: {e}")
            return None

# ==================== ETHERSCAN v2 API (All EVM Chains) ====================

class EtherscanMultiChainFetcher:
    """
    Fetch transactions from EVM chains using Etherscan v2 API
    Uses SINGLE endpoint: https://api.etherscan.io/v2/api with chainid parameter
    """
    
    V2_ENDPOINT = 'https://api.etherscan.io/v2/api'
    
    CHAIN_CONFIGS = {
        'ethereum': {'chainid': 1, 'name': 'Ethereum'},
        'bsc': {'chainid': 56, 'name': 'Binance Smart Chain'},
        'polygon': {'chainid': 137, 'name': 'Polygon'},
        'optimism': {'chainid': 10, 'name': 'Optimism'},
        'arbitrum': {'chainid': 42161, 'name': 'Arbitrum One'},
        'avalanche': {'chainid': 43114, 'name': 'Avalanche'},
        'fantom': {'chainid': 250, 'name': 'Fantom'},
        'base': {'chainid': 8453, 'name': 'Base'},
        'cronos': {'chainid': 25, 'name': 'Cronos'},
        'moonbeam': {'chainid': 1284, 'name': 'Moonbeam'},
        'gnosis': {'chainid': 100, 'name': 'Gnosis'},
        'celo': {'chainid': 42220, 'name': 'Celo'},
        'blast': {'chainid': 81457, 'name': 'Blast'},
        'linea': {'chainid': 59144, 'name': 'Linea'},
        'sepolia': {'chainid': 11155111, 'name': 'Sepolia (Testnet)'},
    }
    
    @staticmethod
    def fetch_transactions(chain: str, address: str, include_internal: bool = True, 
                          include_token_transfers: bool = True) -> Tuple[List[Dict], Dict]:
        
        chain = chain.lower()
        if chain not in EtherscanMultiChainFetcher.CHAIN_CONFIGS:
            # Try BlockScout fallback immediately if chain not supported here but supported there
             return BlockScoutFetcher.fetch_transactions(chain, address)
        
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        transactions = []
        counts = {'normal': 0, 'internal': 0, 'token': 0}
        
        # Fallback to BlockScout if no key
        if not ETHERSCAN_API_KEY:
            print(f"⚠️  No Etherscan API key, using BlockScout for {config['name']}...")
            return BlockScoutFetcher.fetch_transactions(chain, address)
        
        try:
            print(f"[+] Fetching {config['name']} transactions via Etherscan v2 API...")
            
            # Normal transactions
            normal_txs = EtherscanMultiChainFetcher._fetch_page(chain, address, 'txlist')
            transactions.extend(normal_txs)
            counts['normal'] = len(normal_txs)
            
            # Internal transactions
            if include_internal:
                internal_txs = EtherscanMultiChainFetcher._fetch_page(chain, address, 'txlistinternal')
                transactions.extend(internal_txs)
                counts['internal'] = len(internal_txs)
            
            # Token transfers
            if include_token_transfers:
                token_txs = EtherscanMultiChainFetcher._fetch_page(chain, address, 'tokentx')
                transactions.extend(token_txs)
                counts['token'] = len(token_txs)
            
            total = counts['normal'] + counts['internal'] + counts['token']
            print(f"✅ {config['name']}: {counts['normal']} normal, {counts['internal']} internal, {counts['token']} token ({total} total)")
            return transactions, counts
        
        except Exception as e:
            print(f"❌ {config['name']} fetch error: {e}")
            print(f"   Falling back to BlockScout...")
            return BlockScoutFetcher.fetch_transactions(chain, address)
            
    @staticmethod
    def fetch_by_tx_hash(chain: str, tx_hash: str) -> Optional[Dict]:
         """Fetch transaction by hash on EVM chains. Relies on BlockScout fallback for generic tx queries"""
         print(f"[+] Proxying Etherscan TxHash to BlockScout...")
         return BlockScoutFetcher.fetch_by_tx_hash(chain, tx_hash)
    
    @staticmethod
    def _fetch_page(chain: str, address: str, action: str, page: int = 1, offset: int = 5000) -> List[Dict]:
        config = EtherscanMultiChainFetcher.CHAIN_CONFIGS[chain]
        params = {
            'chainid': config['chainid'],
            'module': 'account',
            'action': action,
            'address': address,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': ETHERSCAN_API_KEY
        }
        
        try:
            response = requests.get(EtherscanMultiChainFetcher.V2_ENDPOINT, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('result'):
                # Normalize results
                results = []
                for tx in data['result']:
                    tx['chain'] = chain
                    if 'timeStamp' in tx: # Normalize timestamp format
                        try:
                            tx['timestamp'] = datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                    # Normalize Value (Wei -> ETH)
                    if 'value' in tx:
                        try:
                            tx['value'] = float(tx['value']) / 1e18
                        except:
                            tx['value'] = 0.0
                            
                    results.append(tx)
                return results
            return []
        except:
            return []


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
        if not getblock_key:
            print("⚠️ No GETBLOCK_DOGE_KEY in .env. Falling back to empty response.")
            return [], counts
            
        print(f"[GetBlock.io] Attempting fallback for {address}...")
        url = f"https://go.getblock.io/{getblock_key}/"
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
                    print(f"✅ Dogecoin (GetBlock): {counts['normal']} transactions")
                    return transactions, counts
            else:
                 print(f"❌ GetBlock.io returned status {resp.status_code}")
        except Exception as e:
             print(f"❌ GetBlock.io Error: {e}")
             
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
                print(f"✅ Bitcoin (Mempool): {counts['normal']} transactions")
                return transactions, counts
            else:
                print(f"❌ Mempool API error: {response.status_code}")
                
            return transactions, counts
            
        except Exception as e:
            print(f"❌ Bitcoin fetch error: {e}")
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
            print(f"❌ Bitcoin Tx details Error: {e}")
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
                # print(f"✅ Helius Enhanced API: {len(transactions)} transactions found")
                return transactions, counts
        except Exception as e:
            print(f"⚠️ Helius Enhanced API failed: {e}. Trying Solscan fallback...")

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
                print(f"⚠️  Solscan {resp.status_code}. Trying Public API fallback...")
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
                    print(f"✅ Solscan: {len(transactions)} transactions found")
                    return transactions, counts
            
        except Exception as e:
            print(f"⚠️ Solscan API Error: {e}")

        # 3. Last Resort: Public Solana RPC
        print("⚠️ Helius and Solscan failed. Attempting publicnode last-resort fallback...")
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
                    
                    val = 0.0
                    sender = "Unknown"
                    receiver = "Interaction"
                    
                    # Native transfers
                    for nt in tx.get('nativeTransfers', []):
                        if nt.get('toUserAccount') == address:
                            val += nt.get('amount', 0) / 1e9
                            sender = nt.get('fromUserAccount')
                        if nt.get('fromUserAccount') == address:
                            val += nt.get('amount', 0) / 1e9
                            receiver = nt.get('toUserAccount')
                            sender = address

                    # Balance changes fallback
                    if val == 0:
                        for ad in tx.get('accountData', []):
                            if ad.get('account') == address:
                                val = abs(ad.get('nativeBalanceChange', 0)) / 1e9
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
                print(f"✅ Helius Enhanced: {len(transactions)} transactions found")
                return transactions, counts
            else:
                print(f"⚠️ Helius Enhanced Error: {resp.status_code}")
                return [], counts
        except Exception as e:
            print(f"⚠️ Helius Enhanced Exception: {e}")
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
                                        print(f"⚠️ Rate limited (429) for {sig[:8]}... attempt {attempt+1}/{max_retries}, waiting {wait_time}s...")
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
                                    print(f"⚠️ Failed to fetch detail for {sig}: {sub_e}")
                                    time.sleep(2)
                            
                            # Increased base delay to 1.0s to be very safe
                            time.sleep(1.0)

                except Exception as e:
                    print(f"⚠️ Solana Sequential RPC failed: {e}")

                print(f"✅ Solana RPC: {len(transactions)} transactions found")
                counts['normal'] = len(transactions)
                return transactions, counts
            else:
                print(f"❌ Solana RPC Error: {data.get('error', {})}")
                return [], counts
        except Exception as e:
            print(f"❌ Solana RPC Exception: {e}")
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
            print(f"❌ Solana Tx details Error: {e}")
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
                    print(f"✅ Tron (TronGrid): {counts['normal']} transactions")
                    return transactions, counts
            
            print(f"⚠️ TronGrid Failed ({response.status_code}). Trying TronScan fallback...")
            
        except Exception as e:
            print(f"⚠️ TronGrid Error: {e}")

        # 2. Try TronScan (Public API)
        try:
            print(f"[+] [TronScan] Fetching transactions for {address[:8]}...")
            
            # Pagination Logic
            start = 0
            limit = 50
            total_fetched = 0
            MAX_FETCH = 1000 # Safety limit
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
                    print(f"❌ TronScan Error: {response.status_code}")
                    has_more = False # Stop on error
                    
            counts['normal'] = len(transactions)
            print(f"✅ Tron (TronScan): {counts['normal']} transactions")
            return transactions, counts
                
        except Exception as e:
            print(f"❌ TronScan Exception: {e}")
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
            print(f"❌ Tron Tx details Error: {e}")
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
                        print(f"✅ XRP: {counts['normal']} transactions")
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
                if time_since_last < 86400: # 24 hour cache
                    # Load txs
                    db_txs = db.query(Transaction).filter(
                        (Transaction.from_address == address) | (Transaction.to_address == address)
                    ).order_by(Transaction.timestamp.desc()).limit(500).all()
                    
                    if db_txs:
                        print(f"[MultiChainFetcher] Cache Hit for {address} on {chain}")
                        for t in db_txs:
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
                        db.close()
                        return txs, counts

        db.close()
        print(f"[MultiChainFetcher] Cache Miss/Force Refresh for {address}. Fetching external.")
        
        # 2. External Fetch
        # EVM Chains
        if chain in ['ethereum', 'ethereum', 'eth']:
            return EtherscanMultiChainFetcher.fetch_transactions('ethereum', address, **kwargs)
        elif chain in ['polygon', 'matic']:
            return EtherscanMultiChainFetcher.fetch_transactions('polygon', address, **kwargs)
        elif chain in ['arbitrum', 'arb']:
            return EtherscanMultiChainFetcher.fetch_transactions('arbitrum', address, **kwargs)
        elif chain in ['optimism', 'op']:
            return EtherscanMultiChainFetcher.fetch_transactions('optimism', address, **kwargs)
        elif chain in ['bsc', 'binance', 'bnb']:
            return EtherscanMultiChainFetcher.fetch_transactions('bsc', address, **kwargs)
            
        # Non-EVM Chains (Real Implementations)
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
            
        else:
            print(f"⚠️ Unsupported chain '{chain}', defaulting to empty")
            return [], {}
            
    @staticmethod
    def fetch_tx_by_hash(chain: str, tx_hash: str) -> Optional[Dict]:
        """Universal fetch method for a single transaction hash"""
        chain = chain.lower()
        
        # EVM Chains
        if chain in ['ethereum', 'eth', 'polygon', 'matic', 'arbitrum', 'arb', 'optimism', 'op', 'bsc', 'binance', 'bnb', 'base', 'avalanche', 'fantom', 'cronos', 'moonbeam', 'gnosis', 'celo', 'blast', 'linea', 'sepolia']:
            return EtherscanMultiChainFetcher.fetch_by_tx_hash(chain, tx_hash)
            
        # Non-EVM Chains
        elif chain in ['bitcoin', 'btc']:
            return MempoolFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['solana', 'sol']:
            return SolanaFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['tron', 'trx']:
            return TronFetcher.fetch_by_tx_hash(tx_hash)
        elif chain in ['dogecoin', 'doge']:
            return BlockCypherFetcher.fetch_by_tx_hash(tx_hash)
        
        else:
            print(f"⚠️ Unsupported chain '{chain}' for hash lookup")
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
        }
        return explorers.get(chain, '#')

if __name__ == '__main__':
    print("Test run...")
