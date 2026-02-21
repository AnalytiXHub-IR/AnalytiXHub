from typing import List, Dict, Set
from modules.fetchers.multi_chain import MultiChainFetcher
from modules.utils.helpers import normalize_address

class PathFinder:
    """
    Cross-Wallet Pathfinder
    Finds direct or 1-hop indirect connections between Address A and Address B
    by analyzing the transaction histories of both wallets.
    """
    
    @staticmethod
    def find_path(source: str, target: str, chain: str = "ethereum") -> Dict:
        """
        Calculates intersection between source and target addresses.
        Returns paths found.
        """
        source_norm = normalize_address(source, chain)
        target_norm = normalize_address(target, chain)
        
        results = {
            "source": source,
            "target": target,
            "chain": chain,
            "direct_paths": [],
            "indirect_paths": [],
            "error": None
        }
        
        try:
            # 1. Fetch transactions for both addresses
            source_txs, _ = MultiChainFetcher.fetch_by_chain(chain, source)
            target_txs, _ = MultiChainFetcher.fetch_by_chain(chain, target)
            
            if not source_txs or not target_txs:
                results["error"] = "Insufficient data. One or both addresses have no transactions on this chain."
                return results

            # 2. Analyze Source -> Interactions
            source_sent_to = {}
            source_received_from = {}
            
            for tx in source_txs:
                frm = normalize_address(tx.get('from', ''), chain)
                to = normalize_address(tx.get('to', ''), chain)
                
                # Check Direct Paths immediately
                if frm == source_norm and to == target_norm:
                    results["direct_paths"].append(tx)
                elif frm == target_norm and to == source_norm:
                    results["direct_paths"].append(tx)
                
                if frm == source_norm:
                    if to not in source_sent_to: source_sent_to[to] = []
                    source_sent_to[to].append(tx)
                elif to == source_norm:
                    if frm not in source_received_from: source_received_from[frm] = []
                    source_received_from[frm].append(tx)

            # 3. Analyze Target -> Interactions (for 1-hop intersection)
            for tx in target_txs:
                frm = normalize_address(tx.get('from', ''), chain)
                to = normalize_address(tx.get('to', ''), chain)
                
                # Indirect Path 1: Source -> Intermediate -> Target
                if to == target_norm and frm in source_sent_to:
                    results["indirect_paths"].append({
                        "type": "Source -> Intermediate -> Target",
                        "intermediate_node": frm,
                        "tx_source_to_inter": source_sent_to[frm][0], # Simplified
                        "tx_inter_to_target": tx
                    })
                
                # Indirect Path 2: Target -> Intermediate -> Source
                if frm == target_norm and to in source_received_from:
                    results["indirect_paths"].append({
                        "type": "Target -> Intermediate -> Source",
                        "intermediate_node": to,
                        "tx_target_to_inter": tx,
                        "tx_inter_to_source": source_received_from[to][0]
                    })
                    
            # Deduplicate indirect paths
            unique_indirects = {}
            for p in results["indirect_paths"]:
                key = f"{p['type']}_{p['intermediate_node']}"
                if key not in unique_indirects:
                    unique_indirects[key] = p
                    
            results["indirect_paths"] = list(unique_indirects.values())

            return results
            
        except Exception as e:
            results["error"] = str(e)
            return results
