
from sqlalchemy import func
from db_models import SessionLocal, Transaction, Address, Case

def get_visualization_data(case_id):
    db = SessionLocal()
    try:
        case = db.query(Case).filter_by(case_id=case_id).first()
        if not case: return None
        
        # 1. Transaction Volume Over Time (Group by Day)
        # SQLite doesn't have date_trunc, use strftime
        vol_data = db.query(
            func.strftime('%Y-%m-%d', Transaction.timestamp).label('date'),
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('volume')
        ).join(Address, (Transaction.from_address == Address.address) | (Transaction.to_address == Address.address))\
         .filter(Address.case_id == case.id)\
         .group_by('date').order_by('date').all()
         
        timeline_chart = {
            "labels": [r.date for r in vol_data],
            "counts": [r.count for r in vol_data],
            "volumes": [r.volume for r in vol_data]
        }
        
        # 2. Risk Distribution
        risk_data = db.query(
            Address.label, 
            Address.risk_score
        ).filter(Address.case_id == case.id).all()
        
        risk_dist = {"High": 0, "Medium": 0, "Low": 0}
        for r in risk_data:
            score = r.risk_score
            if score >= 70: risk_dist["High"] += 1
            elif score >= 30: risk_dist["Medium"] += 1
            else: risk_dist["Low"] += 1
            
        # 3. Flow (Sankey) - Simplified top interactions
        # Top sender -> receiver pairs
        # This is complex, let's just get top 20 edges
        # We need to filter txs where at least one side is in the case
        edges = db.query(
            Transaction.from_address,
            Transaction.to_address,
            func.sum(Transaction.amount).label('value')
        ).join(Address, (Transaction.from_address == Address.address) | (Transaction.to_address == Address.address))\
         .filter(Address.case_id == case.id)\
         .group_by(Transaction.from_address, Transaction.to_address)\
         .order_by(func.sum(Transaction.amount).desc())\
         .limit(20).all()
         
        sankey_data = {
            "nodes": [],
            "links": []
        }
        
        node_map = {}
        def get_node_idx(addr):
            if addr not in node_map:
                node_map[addr] = len(sankey_data["nodes"])
                sankey_data["nodes"].append({"name": addr[:8] + "..."})
            return node_map[addr]
            
        for e in edges:
            src = get_node_idx(e.from_address)
            dst = get_node_idx(e.to_address)
            sankey_data["links"].append({
                "source": src,
                "target": dst,
                "value": e.value
            })
            
        return {
            "timeline": timeline_chart,
            "risk": risk_dist,
            "sankey": sankey_data
        }
    finally:
        db.close()
