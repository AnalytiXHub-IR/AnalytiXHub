import requests
import time

# Use the Etherscan V2 API endpoint (per migration guidance)
ETHERSCAN_API = "https://api.etherscan.io/v2/api"

# Supported chains mapping
SUPPORTED_CHAINS = {
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
    # Non-EVM Chains (Internal IDs for Normalization)
    "solana": -1,
    "sol": -1,
    "bitcoin": -2,
    "btc": -2,
    "tron": -3,
    "trx": -3,
    "xrp": -4,
    "ripple": -4,
}

def _validate_chain(chain_id):
    """Validate chain_id is an integer"""
    if not isinstance(chain_id, (int, str)):
        raise ValueError(f"Invalid chain_id type: {type(chain_id)}")
    try:
        chain_id = int(chain_id)
        # Allow negative IDs for internal non-EVM use
        # Upper bound check only
        if chain_id > 999999999: 
            # Very loose upper bound
            pass
        return chain_id
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid chain_id: {chain_id}") from e

def _fetch_page(address, api_key, chain_id=1, page=1, offset=1000, action="txlist", startblock=0, endblock=99999999):
    """Fetch a page of transactions from Etherscan V2 API for a specific chain"""
    chain_id = _validate_chain(chain_id)
    
    params = {
        "chainid": str(chain_id),
        "module": "account",
        "action": action,
        "address": address,
        "startblock": startblock,
        "endblock": endblock,
        "page": page,
        "offset": offset,
        "sort": "asc",
        "apikey": api_key
    }

    r = requests.get(ETHERSCAN_API, params=params, timeout=15)
    return r.json()


def _fetch_all_paginate_by_block(address, api_key, chain_id, action, max_txs=None):
    all_txs = []
    seen = set()
    startblock = 0
    offset = 10000  # Max Etherscan allows per page
    
    while True:
        if max_txs and len(all_txs) >= max_txs:
            break
            
        data = _fetch_page(address, api_key, chain_id=chain_id, page=1, offset=offset, action=action, startblock=startblock)
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
                all_txs.append(tx)
                added_in_page += 1
                
        if len(page_results) < offset:
            break
            
        # Over 10k, slide block
        last_tx = page_results[-1]
        new_startblock = int(last_tx.get('blockNumber', startblock))
        if new_startblock == startblock and added_in_page == 0:
            print("[ETHERSCAN API] Stuck on giant block, breaking.")
            break
        startblock = new_startblock
        time.sleep(0.25)
        
    return all_txs

def fetch_eth_address(address, api_key, chain_id=1, include_internal=False, include_token_transfers=False, max_txs=None, startblock=0):
    """Fetch full transaction history for an address from Etherscan V2 API (Unlimited via block pagination)."""
    if not api_key:
        raise Exception("Missing Etherscan API key")

    chain_id = _validate_chain(chain_id)
    all_txs = []

    try:
        normals = _fetch_all_paginate_by_block(address, api_key, chain_id, action="txlist", max_txs=max_txs, startblock=startblock)
        all_txs.extend(normals)

        if include_internal:
            internals = _fetch_all_paginate_by_block(address, api_key, chain_id, action="txlistinternal", max_txs=max_txs, startblock=startblock)
            all_txs.extend(internals)

        if include_token_transfers:
            tokens = _fetch_all_paginate_by_block(address, api_key, chain_id, action="tokentx", max_txs=max_txs, startblock=startblock)
            all_txs.extend(tokens)

        return all_txs
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network connection failed: {e}")

def fetch_eth_address_with_counts(address, api_key, chain_id=1, include_internal=False, include_token_transfers=False, startblock=0):
    """Returns combined tx list and a breakdown of counts per type (Unlimited via block pagination)."""
    if not api_key:
        raise Exception("Missing Etherscan API key")

    chain_id = _validate_chain(chain_id)
    counts = {'normal': 0, 'internal': 0, 'token': 0}
    combined = []

    normals = _fetch_all_paginate_by_block(address, api_key, chain_id, action="txlist", startblock=startblock)
    counts['normal'] = len(normals)
    combined.extend(normals)

    if include_internal:
        internals = _fetch_all_paginate_by_block(address, api_key, chain_id, action="txlistinternal", startblock=startblock)
        counts['internal'] = len(internals)
        combined.extend(internals)

    if include_token_transfers:
        tokens = _fetch_all_paginate_by_block(address, api_key, chain_id, action="tokentx", startblock=startblock)
        counts['token'] = len(tokens)
        combined.extend(tokens)

    return combined, counts

def fetch_transaction_details(tx_hash, api_key, chain_id=1):
    """Fetch details of a specific transaction."""
    chain_id = _validate_chain(chain_id)
    
    params = {
        "chainid": str(chain_id),
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": tx_hash,
        "apikey": api_key
    }
    
    try:
        r = requests.get(ETHERSCAN_API, params=params, timeout=10)
        data = r.json()
        
        if data.get('result'):
            return data['result']
        return None
        
    except Exception as e:
        print(f"Error fetching tx {tx_hash}: {e}")
        return None