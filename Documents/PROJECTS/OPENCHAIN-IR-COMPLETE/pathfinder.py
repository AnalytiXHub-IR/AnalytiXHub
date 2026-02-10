from typing import List, Dict, Set, Optional
from breadcrumbs_client import BreadcrumbsClient
import concurrent.futures

class PathFinder:
    """
    Breadcrumbs-style PathFinder engine.
    Finds transaction paths between Source and Destination addresses.
    """
    
    def __init__(self):
        self.client = BreadcrumbsClient()

    def find_path(self, source: str, target: str, chain_id: int = 1, max_depth: int = 3) -> Dict:
        """
        BFS to find path from source to target.
        Returns a cytoscape-compatible element list representing the path.
        """
        source = source.lower()
        target = target.lower()
        
        # Bi-directional search could be better, but simple BFS is safer for API limits
        queue = [(source, [source])] # (current_addr, path)
        visited = {source}
        
        # We need to fetch data. 
        # Since real API is slow, we limit width and depth aggressively.
        
        # For DEMO purposes: 
        # If we can't find a real path quickly, we might simulate one if it's a known scenario,
        # otherwise we traverse.
        
        found_paths = []
        
        print(f"[PathFinder] Searching {source} -> {target} (Max Depth: {max_depth})")
        
        # Level 1: Check direct connection
        src_data = self.client.get_graph_data(source, chain_id)
        if self._check_connection(src_data, target, found_paths, source):
            return self._build_graph(found_paths)
            
        # Level 2: Expand neighbors (limited)
        # Get top 5 high-value neighbors to avoid exploding API limits
        neighbors = self._get_top_neighbors(src_data)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_addr = {executor.submit(self.client.get_graph_data, n, chain_id): n for n in neighbors}
            for future in concurrent.futures.as_completed(future_to_addr):
                addr = future_to_addr[future]
                try:
                    data = future.result()
                    if self._check_connection(data, target, found_paths, addr, parent=source):
                        print(f"[PathFinder] Found path via {addr}")
                except Exception as e:
                    print(f"Error checking {addr}: {e}")
                    
        if found_paths:
             return self._build_graph(found_paths)
             
        return {"error": "No direct path found within search limits."}

    def _get_top_neighbors(self, elements):
        neighbors = []
        for el in elements:
            if 'source' in el['data']:
                # It's an edge
                target = el['data']['target']
                if target not in neighbors:
                    neighbors.append(target)
        return neighbors[:5] # Limit to top 5

    def _check_connection(self, elements, target, found_paths, current_node, parent=None):
        found = False
        for el in elements:
            if 'source' in el['data']:
                t = el['data']['target']
                if t == target:
                    # Found it!
                    found_paths.append(el) # Add the edge
                    if parent:
                        # Add parent edge if we have the data? 
                        # This simplified logic assumes we reconstruct the full path later
                        pass
                    found = True
        return found
        
    def _build_graph(self, paths):
        """Reconstruct the graph from found paths"""
        elements = []
        nodes = set()
        
        for edge in paths:
            s = edge['data']['source']
            t = edge['data']['target']
            
            # Add nodes
            if s not in nodes:
                elements.append({'data': {'id': s, 'label': f"{s[:6]}...", 'full_address': s, 'type': 'entity', 'icon': "https://img.icons8.com/fluency/48/000000/user-location.png"}})
                nodes.add(s)
            if t not in nodes:
                elements.append({'data': {'id': t, 'label': f"{t[:6]}...", 'full_address': t, 'type': 'target', 'icon': "https://img.icons8.com/fluency/48/000000/target.png"}})
                nodes.add(t)
                
            # Add edge
            elements.append(edge)
            
        return elements
