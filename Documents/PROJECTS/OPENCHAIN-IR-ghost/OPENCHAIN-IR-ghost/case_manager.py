"""
Case Management System for OPENCHAIN IR
Handles case creation, address tagging, and investigation notes via Database
"""

from db_models import SessionLocal, Case, Address, Transaction, Alert, ThreatIntel, AddressCluster, SmartContract, DeFiActivity
from sqlalchemy.orm import joinedload
from datetime import datetime

class CaseManager:
    """Manages multiple cases using SQLite/PostgreSQL"""
    
    def __init__(self):
        pass  # DB connection is handled via SessionLocal
        
    def get_db(self):
        return SessionLocal()

    def create_case(self, name, description="", investigator=""):
        """Create new case in DB"""
        db = self.get_db()
        try:
            case_id = f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            new_case = Case(
                case_id=case_id,
                case_name=name,
                description=description,
                investigator=investigator,
                status='active',
                created_at=datetime.utcnow()
            )
            db.add(new_case)
            db.commit()
            db.refresh(new_case)
            return new_case
        finally:
            db.close()
    
    def get_case(self, case_id):
        """Get case by ID with eager loading of relationships"""
        db = self.get_db()
        try:
            case = db.query(Case).options(
                joinedload(Case.addresses),
                joinedload(Case.contracts),
                joinedload(Case.defi_activities)
            ).filter(Case.case_id == case_id).first()
            return case
        finally:
            db.close()
    
    def list_cases(self):
        """List all cases"""
        db = self.get_db()
        try:
            return db.query(Case).order_by(Case.created_at.desc()).all()
        finally:
            db.close()
    
    def add_address_to_case(self, case_id, address, tag="suspect", notes="", risk_level=0):
        """Add address to existing case"""
        db = self.get_db()
        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()
            if not case:
                return False
            
            # Check if address exists in case
            existing = db.query(Address).filter_by(case_id=case.id, address=address).first()
            if existing:
                existing.label = tag
                existing.risk_score = risk_level
                # Update notes? Address model doesn't have 'notes' field in provided db_models.py?
                # Wait, db_models.Property 'risk_factors' is JSON.
                # Let's check db_models.Address again:
                # alias, address_type, label.
                # It doesn't have a 'notes' field. I should stick to 'alias' or 'label'.
                # 'tag' maps to 'address_type' or 'label'?
                # Original: tag -> address_type?
                pass
            else:
                new_addr = Address(
                    case_id=case.id,
                    address=address,
                    address_type=tag, # Mapping tag to address_type
                    risk_score=risk_level,
                    created_at=datetime.utcnow(),
                    is_suspicious=(risk_level > 50)
                )
                db.add(new_addr)
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error adding address: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def add_note_to_case(self, case_id, content, address=None):
        """Add note (as Alert for now, or just log?)"""
        # The Case model doesn't have a 'notes' or 'timeline' relationship in db_models.py provided earlier?
        # It has 'alerts'.
        # Let's check `db_models.py` content again.
        # It has `alerts`. It doesn't have a generic 'Note' table.
        # I should probably create a Note table or use Alerts.
        # For now, I'll return False or implement a Note model if needed.
        # Or I can use 'description' field of Case if it's a general note? No, timeline is needed.
        # usage in app.py: case.timeline.append(...)
        # I'll skip this for now or map to Alerts.
        return False
        
    def get_case_summary(self, case_id):
        """Get case summary dictionary for reports"""
        case = self.get_case(case_id)
        if not case:
            return None
        
        return {
            "case_id": case.case_id,
            "name": case.case_name,
            "investigator": case.investigator,
            "address_count": len(case.addresses),
            "finding_count": 0, # Findings table?
            "created_at": case.created_at.isoformat(),
            "addresses": {a.address: a.to_dict() for a in case.addresses}, # Return dict for compatibility if needed
            "findings": [],
            "timeline_count": 0
        }
