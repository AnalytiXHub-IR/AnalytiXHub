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
}

def _validate_chain(chain_id):
    """Validate chain_id is an integer between 1 and 11155111"""
    if not isinstance(chain_id, (int, str)):
        raise ValueError(f"Invalid chain_id type: {type(chain_id)}")
    try:
        chain_id = int(chain_id)
        if chain_id < 1 or chain_id > 11155111:
            raise ValueError(f"Chain ID {chain_id} out of supported range")
        return chain_id
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid chain_id: {chain_id}") from e

def _fetch_page(address, api_key, chain_id=1, page=1, offset=1000, action="txlist"):
    """Fetch a page of transactions from Etherscan V2 API for a specific chain"""
    chain_id = _validate_chain(chain_id)
    
    params = {
        "chainid": str(chain_id),
        "module": "account",
        "action": action,
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": page,
        "offset": offset,
        "sort": "asc",
        "apikey": api_key
    }

    r = requests.get(ETHERSCAN_API, params=params, timeout=15)
    return r.json()


def fetch_eth_address(address, api_key, chain_id=1, include_internal=False, include_token_transfers=False):
    """Fetch full transaction history for an address from Etherscan V2 API.

    Args:
        address: Blockchain address (0x...)
        api_key: Etherscan API key
        chain_id: Chain ID (1=Ethereum, 56=BSC, 137=Polygon, etc.)
        include_internal: Include internal transactions
        include_token_transfers: Include ERC-20 transfers

    This performs paginated requests and will return a combined list of normal
    transactions. Set `include_internal` or `include_token_transfers` to True to
    also fetch internal transactions and ERC-20 transfers (additional API calls).
    """
    if not api_key:
        raise Exception("Missing Etherscan API key")

    chain_id = _validate_chain(chain_id)
    all_txs = []
    page = 1
    offset = 1000  # page size; adjust as needed but keep reasonable for rate limits

    try:
        while True:
            data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="txlist")
            # Etherscan returns a 'status' and 'message' field
            if data.get('status') == '0' and data.get('message') != 'OK':
                # no transactions or an error
                if data.get('result') == 'No transactions found':
                    break
                print(f"[ETHERSCAN API] {data.get('message')} - {data.get('result')}")
                break

            page_results = data.get('result', []) or []
            if not page_results:
                break

            all_txs.extend(page_results)

            # If fewer results than offset, we've reached the end
            if len(page_results) < offset:
                break

            page += 1
            time.sleep(0.25)  # be gentle with rate limits

        # Optionally fetch internal txs (may include contract/internal transfers)
        if include_internal:
            page = 1
            while True:
                data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="txlistinternal")
                if data.get('status') == '0' and data.get('message') != 'OK':
                    break
                page_results = data.get('result', []) or []
                if not page_results:
                    break
                all_txs.extend(page_results)
                if len(page_results) < offset:
                    break
                page += 1
                time.sleep(0.25)

        # Optionally fetch ERC20 token transfers
        if include_token_transfers:
            page = 1
            while True:
                data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="tokentx")
                if data.get('status') == '0' and data.get('message') != 'OK':
                    break
                page_results = data.get('result', []) or []
                if not page_results:
                    break
                all_txs.extend(page_results)
                if len(page_results) < offset:
                    break
                page += 1
                time.sleep(0.25)

        return all_txs

    except requests.exceptions.RequestException as e:
        raise Exception(f"Network connection failed: {e}")


def fetch_eth_address_with_counts(address, api_key, chain_id=1, include_internal=False, include_token_transfers=False):
    """Returns combined tx list and a breakdown of counts per type.

    Args:
        address: Blockchain address (0x...)
        api_key: Etherscan API key
        chain_id: Chain ID (1=Ethereum, 56=BSC, 137=Polygon, etc.)
        include_internal: Include internal transactions
        include_token_transfers: Include ERC-20 transfers

    Returns: (all_txs_list, counts_dict)
    counts_dict = {'normal': int, 'internal': int, 'token': int}
    """
    if not api_key:
        raise Exception("Missing Etherscan API key")

    chain_id = _validate_chain(chain_id)

    counts = {'normal': 0, 'internal': 0, 'token': 0}
    combined = []

    # Fetch normal transactions (paginated) and count
    page = 1
    offset = 1000
    while True:
        data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="txlist")
        if data.get('status') == '0' and data.get('message') != 'OK':
            if data.get('result') == 'No transactions found':
                break
            break
        page_results = data.get('result', []) or []
        if not page_results:
            break
        counts['normal'] += len(page_results)
        combined.extend(page_results)
        if len(page_results) < offset:
            break
        page += 1
        time.sleep(0.25)

    if include_internal:
        page = 1
        while True:
            data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="txlistinternal")
            if data.get('status') == '0' and data.get('message') != 'OK':
                break
            page_results = data.get('result', []) or []
            if not page_results:
                break
            counts['internal'] += len(page_results)
            combined.extend(page_results)
            if len(page_results) < offset:
                break
            page += 1
            time.sleep(0.25)

    if include_token_transfers:
        page = 1
        while True:
            data = _fetch_page(address, api_key, chain_id=chain_id, page=page, offset=offset, action="tokentx")
            if data.get('status') == '0' and data.get('message') != 'OK':
                break
            page_results = data.get('result', []) or []
            if not page_results:
                break
            counts['token'] += len(page_results)
            combined.extend(page_results)
            if len(page_results) < offset:
                break
            page += 1
            time.sleep(0.25)

    return combined, counts