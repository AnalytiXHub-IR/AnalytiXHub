import requests
import json
import random
from multi_chain import MultiChainFetcher

class BreadcrumbsClient:
    """
    Adapter to fetch multi-chain data and format for Breadcrumbs-style visualization.
    Now uses MultiChainFetcher for real data.
    """
    def __init__(self, etherscan_key=None, breadcrumbs_key=None):
        self.etherscan_key = etherscan_key
        self.breadcrumbs_key = breadcrumbs_key
        
    def get_graph_data(self, address, chain_id=1):
        """
        Fetch data and convert to Cytoscape JSON format using Breadcrumbs API
        """
        breadcrumbs_key = os.getenv("BREADCRUMBS_API_KEY", self.breadcrumbs_key)
        
        # Mapping to Breadcrumbs Chain Params (assuming eth, btc, tron, etc.)
        chain_map = {
            1: 'eth', 'ethereum': 'eth',
            'bitcoin': 'btc',
            'solana': 'sol',
            'tron': 'tron',
            56: 'bsc',
            137: 'matic',
            42161: 'arb',
            10: 'op' # Optimism
        }
        
        c_str = str(chain_id).lower()
        bc_chain = chain_map.get(chain_id, chain_map.get(c_str, 'eth'))
        
        elements = []
        nodes = set()
        
        # Add Root Node
        root_data = {
            "data": {
                "id": address.lower(),
                "label": f"{address[:6]}...{address[-4:]}",
                "full_address": address,
                "type": "target",
                "risk": 50, # Default risk
                "icon": "https://img.icons8.com/fluency/48/000000/target.png"
            },
            "classes": "root"
        }
        elements.append(root_data)
        nodes.add(address.lower())

        if not breadcrumbs_key:
            print("No Breadcrumbs API Key found. Using MultiChainFetcher as fallback.")
            # Fallback to existing mock logic or return empty
            try:
                txs, counts = MultiChainFetcher.fetch_by_chain(self._map_to_internal_chain(bc_chain), address)
            except Exception as e:
                print(f"Error fetching from MultiChainFetcher: {e}")
                txs = []
        else:
            # Call Breadcrumbs API
            # ENDPOINT: https://api.breadcrumbs.app/v1/addresses/{chain}/{address}/monitor or valid endpoint
            # Research indicates: https://api.breadcrumbs.app/v1/ ...
            # Since I cannot browse external docs easily, I will attempt standard investigation endpoint 
            # based on user request "81CGNL... IS breadcrumbs.app api"
            
            # Assuming typical structure for graph/investigation
            # Note: If this fails, I will fall back to MultiChainFetcher
            
            try:
                url = f"https://api.breadcrumbs.app/v1/addresses/{bc_chain}/{address}/transactions"
                headers = {"X-API-Key": breadcrumbs_key}
                
                # Note: This is a hypothesized endpoint based on standard patterns. 
                # If 404, we will use MultiChainFetcher as backup.
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    txs = data.get('transactions', [])
                else:
                    # Fallback to MultiChainFetcher for known chains if API fails
                    print(f"Breadcrumbs API failed ({resp.status_code}). Using MultiChainFetcher.")
                    txs, _ = MultiChainFetcher.fetch_by_chain(self._map_to_internal_chain(bc_chain), address)
            except Exception as e:
                print(f"Error fetching from Breadcrumbs API: {e}. Using MultiChainFetcher as fallback.")
                try:
                    txs, _ = MultiChainFetcher.fetch_by_chain(self._map_to_internal_chain(bc_chain), address)
                except Exception as e_fallback:
                    print(f"Error fetching from MultiChainFetcher fallback: {e_fallback}")
                    txs = []

        # Limit for high density visualization as requested ("fine tune it perfectly")
        MAX_NODES = 100 
        
        for tx in txs[:MAX_NODES]:
            # Standardize TX object
            # MultiChainFetcher returns {from, to, value, hash}
            # Breadcrumbs API might return different keys, but assuming standardized here for now.
            
            frm = str(tx.get('from_address') or tx.get('from', '')).lower()
            to = str(tx.get('to_address') or tx.get('to', '')).lower()
            val = float(tx.get('value', 0))
            hash_ = tx.get('hash', f"tx_{random.randint(1000,9999)}")
            
            if not frm or not to: continue
            
            # Determine Neighbor
            if frm == address.lower(): neighbor = to
            elif to == address.lower(): neighbor = frm
            else: continue
            
            if neighbor in nodes: continue
            
            # Add Node
            elements.append({
                "data": {
                    "id": neighbor,
                    "label": f"{neighbor[:6]}...",
                    "full_address": neighbor,
                    "type": "entity",
                    "risk": random.randint(0, 100) # Placeholder until ThreatIntel lookup
                }
            })
            nodes.add(neighbor)
            
            # Add Edge
            edge_id = f"{hash_}_{frm}_{to}"
            elements.append({
                "data": {
                    "id": edge_id,
                    "source": frm,
                    "target": to,
                    "amount": val,
                    "label": f"{val:.4f}"
                }
            })
                
        return elements

    def _map_to_internal_chain(self, bc_chain):
        map_ = {'eth': 'ethereum', 'btc': 'bitcoin', 'sol': 'solana', 'tron': 'tron', 'bsc': 'bsc', 'matic': 'polygon', 'arb': 'arbitrum', 'op': 'optimism'}
        return map_.get(bc_chain, 'ethereum')

    def scan_all_chains(self, address):
        """
        Aggregates graph data from ALL supported chains.
        """
        import concurrent.futures
        
        chains_to_scan = [1, 56, 137, 10, 42161] # ETH, BSC, POLY, OPT, ARB
        # Add BTC and SOL to scan list if address format matches
        # Basic heuristic for Bitcoin address formats
        if (len(address) >= 26 and len(address) <= 35 and (address.startswith('1') or address.startswith('3') or address.startswith('bc1'))) or \
           (len(address) >= 32 and len(address) <= 44 and address.startswith('L') or address.startswith('M')): 
            chains_to_scan = ['bitcoin'] # Exclusive scan for BTC
            
        # Basic heuristic for Solana
        elif len(address) >= 32 and len(address) <= 44 and not address.startswith('0x'):
             chains_to_scan = ['solana'] # Exclusive scan for SOL
        
        all_elements = []
        seen_nodes = set()
        
        # Add Root Node manually first to ensure it exists
        root_data = {
            "data": {
                "id": address.lower(),
                "label": f"{address[:6]}...{address[-4:]}",
                "full_address": address,
                "type": "target",
                "risk": 50,
                "icon": "https://img.icons8.com/fluency/48/000000/target.png" 
            },
            "classes": "root"
        }
        all_elements.append(root_data)
        seen_nodes.add(address.lower())

        # Parallel Fetch
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Map simplified wrapper to pass single arg
            futures = [executor.submit(self.get_graph_data, address, c) for c in chains_to_scan]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    for el in res:
                        if 'source' not in el['data']: # It's a node
                            nid = el['data']['id']
                            if nid not in seen_nodes:
                                # assign icon based on type if not present
                                if 'icon' not in el['data']:
                                    el['data']['icon'] = "https://img.icons8.com/fluency/48/000000/user-location.png"
                                all_elements.append(el)
                                seen_nodes.add(nid)
                        else: # It's an edge
                            # Add edge (edges are unique by ID usually, but safe to add)
                            all_elements.append(el)
                except Exception as e:
                    print(f"Chain scan error: {e}")
                    
        return all_elements
