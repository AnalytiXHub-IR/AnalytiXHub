
import networkx as nx
from db_models import SessionLocal, Transaction, Address
import community.community_louvain as community_louvain # python-louvain

class GraphIntelligence:
    def __init__(self):
        pass
        
    def build_case_graph(self, case_id):
        """Build NetworkX graph for a case"""
        db = SessionLocal()
        try:
            # Fetch all txs involving case addresses
            # For simplicity, we fetch all txs linked to case addresses
            # Optimization: Fetch via Case relationship if possible, but Transaction is linked to case?
            # Existing model: Transaction.case_id
            
            txs = db.query(Transaction).filter_by(case_id=case_id).all()
            
            G = nx.DiGraph()
            
            for tx in txs:
                G.add_edge(tx.from_address, tx.to_address, 
                           weight=tx.amount, 
                           hash=tx.tx_hash,
                           timestamp=tx.timestamp)
                           
            return G
        finally:
            db.close()
            
    def detect_communities(self, case_id):
        """Detect clusters (e.g. scam rings) using Louvain"""
        G = self.build_case_graph(case_id)
        if len(G.nodes) == 0: return {}
        
        # Louvain requires undirected for standard impl, or convert
        G_undir = G.to_undirected()
        partition = community_louvain.best_partition(G_undir)
        
        # Invert: {community_id: [nodes]}
        communities = {}
        for node, comm_id in partition.items():
            if comm_id not in communities:
                communities[comm_id] = []
            communities[comm_id].append(node)
            
        return communities
        
    def find_laundering_paths(self, case_id, target_address, min_hops=2, max_hops=5):
        """Find paths from target to known high-risk entities (Mixers/Exchanges)"""
        # 1. Build Graph
        G = self.build_case_graph(case_id)
        
        # 2. Identify High Risk Nodes in Graph
        db = SessionLocal()
        try:
             # Get all addresses in graph
             nodes = list(G.nodes)
             # Check distinct addresses in DB for labels
             risk_nodes = db.query(Address).filter(
                 Address.address.in_(nodes),
                 Address.address_type.in_(['Mixer', 'Exchange', 'Ransomware'])
             ).all()
             
             targets = [r.address for r in risk_nodes]
             
             paths = []
             if target_address not in G: return []
             
             for dest in targets:
                 if dest == target_address: continue
                 try:
                     # Find all simple paths
                     for path in nx.all_simple_paths(G, source=target_address, target=dest, cutoff=max_hops):
                         paths.append(path)
                 except:
                     pass
                     
             return paths
        finally:
            db.close()

    def get_cytoscape_elements(self, case_id):
        """Export graph to Cytoscape.js JSON format with rich metadata"""
        G = self.build_case_graph(case_id)
        elements = []
        
        db = SessionLocal()
        try:
            # Pre-fetch all addresses for metadata lookup
            nodes = list(G.nodes)
            addr_objs = db.query(Address).filter(Address.address.in_(nodes)).all()
            addr_map = {a.address: a for a in addr_objs}
            
            # Nodes
            for node in G.nodes:
                addr_data = addr_map.get(node)
                
                # Determine Label & Type
                label = node[:6] + "..." + node[-4:]
                entity_type = "wallet"
                risk_score = 0
                
                if addr_data:
                    if addr_data.entity_name:
                        label = addr_data.entity_name
                    if addr_data.address_type:
                        entity_type = addr_data.address_type.lower()
                    if addr_data.risk_score:
                        risk_score = addr_data.risk_score
                
                # Special Case: High value nodes often exchanges
                # We can refine this with real intelligence data later
                
                elements.append({
                    "data": {
                        "id": node, 
                        "label": label,
                        "full_address": node,
                        "risk": risk_score,
                        "type": entity_type,
                        "degree": G.degree(node)
                    }
                })
                
            # Edges
            for u, v, data in G.edges(data=True):
                elements.append({
                    "data": {
                        "source": u, 
                        "target": v,
                        "weight": float(data.get('weight', 0)),
                        "hash": data.get('hash', ''),
                        "formatted_val": f"{float(data.get('weight', 0)):.4f}"
                    }
                })
                
            return elements
        finally:
            db.close()

    def expand_node(self, address, limit=10):
        """Fetch neighbor transactions for a node to expand graph"""
        db = SessionLocal()
        try:
            # Find txs where address is sender or receiver
            txs = db.query(Transaction).filter(
                (Transaction.from_address == address) | (Transaction.to_address == address)
            ).limit(limit).all()
            
            elements = []
            
            # Helper to get/create node metadata
            def get_node_data(addr):
                # Try to get from DB
                a_obj = db.query(Address).filter_by(address=addr).first()
                label = addr[:6] + "..." + addr[-4:]
                risk = 0
                atype = "wallet"
                
                if a_obj:
                    if a_obj.entity_name: label = a_obj.entity_name
                    if a_obj.risk_score: risk = a_obj.risk_score
                    if a_obj.address_type: atype = a_obj.address_type.lower()
                    
                return {
                    "id": addr,
                    "label": label,
                    "full_address": addr,
                    "risk": risk,
                    "type": atype
                }

            # Add the central node if needed (client usually handles, but safe to send)
            # elements.append({"data": get_node_data(address)})

            for tx in txs:
                # Determine neighbor
                other = tx.to_address if tx.from_address == address else tx.from_address
                
                # Add Neighbor Node
                elements.append({"data": get_node_data(other)})
                
                # Add Edge
                elements.append({
                    "data": {
                        "source": tx.from_address,
                        "target": tx.to_address,
                        "weight": float(tx.amount),
                        "hash": tx.tx_hash,
                        "formatted_val": f"{float(tx.amount):.4f}"
                    }
                })
                
            return elements
        finally:
            db.close()



    # ================== DEMIXING TOOLS ==================

    def detect_coinjoin(self, tx_hash):
        """
        Detect CoinJoin pattern: Multiple inputs, multiple outputs of equal value.
        """
        db = SessionLocal()
        try:
            tx = db.query(Transaction).filter_by(tx_hash=tx_hash).first()
            if not tx: return {"is_coinjoin": False, "reason": "Tx not found"}
            
            # To detect CoinJoin real-time, we need full input/output list.
            # Our current simplified model captures 'from' and 'to' and 'amount'.
            # A real CoinJoin has MANY inputs and MANY outputs.
            # If our DB/App stores single-row per transfer, we need to aggregate by Hash.
            
            same_hash_txs = db.query(Transaction).filter_by(tx_hash=tx_hash).all()
            
            if len(same_hash_txs) < 3:
                return {"is_coinjoin": False, "reason": "Too few participants"}
                
            # Check for equal output amounts
            outputs = [t.amount for t in same_hash_txs]
            # If >50% of outputs are identical, likely a mix
            from collections import Counter
            counts = Counter(outputs)
            most_common_amt, count = counts.most_common(1)[0]
            
            if count > len(outputs) * 0.5 and len(outputs) > 2:
                return {
                    "is_coinjoin": True, 
                    "confidence": 0.9, 
                    "mixing_amount": most_common_amt,
                    "participants": len(outputs)
                }
                
            return {"is_coinjoin": False, "reason": "No equal output structure"}
        finally:
            db.close()

    def detect_peel_chain(self, root_address, depth=5):
        """
        Detect Peel Chain: Large input -> Small Payment + Large Change (recursively)
        """
        db = SessionLocal()
        try:
            current = root_address
            chain = []
            
            for _ in range(depth):
                # Find outgoing txs from current
                txs = db.query(Transaction).filter_by(from_address=current).all()
                if not txs: break
                
                # Look for the pattern: 1 small output, 1 large change output (approx 90%+ of total)
                # Sort by amount descending
                txs.sort(key=lambda x: x.amount, reverse=True)
                
                if len(txs) >= 1:
                    largest = txs[0]
                    # If this is a "change" address, it should be a new address (conceptually)
                    # And there should be smaller payments.
                    
                    # For simple pattern matching, we just trace the largest volume path
                    chain.append({
                        "hop": current,
                        "tx": largest.tx_hash,
                        "next": largest.to_address,
                        "amount": largest.amount
                    })
                    current = largest.to_address
                else:
                    break
            
            return {
                "is_peel_chain": len(chain) >= 3,
                "chain": chain
            }
        finally:
            db.close()

# Global Instance
graph_intel = GraphIntelligence()
