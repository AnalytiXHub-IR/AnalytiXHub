
import sqlite3
from datetime import datetime
from db_models import SessionLocal, Address

class ThreatIntel:
    def __init__(self):
        self._seed_db()

    def _seed_db(self):
        """Seed specific known malicious actors into the DB"""
        db = SessionLocal()
        try:
            # Known Entities (Mock Data based on real world)
            seeds = [
                ("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "Vitalik Buterin", "Individual", "Low"),
                ("0x77696bb39917c91a5464507f3693fb6826372cae", "Mixer: Tornado Cash", "Mixer", "High"),
                ("0xFakeHackAddress123", "Lazarus Group (Mock)", "Cybercriminal", "Critical"),
                ("0xFakeScamAddress456", "Phishing Campaign #92", "Scammer", "High")
            ]
            
            for addr, label, type_, risk in seeds:
                existing = db.query(Address).filter_by(address=addr).first()
                if not existing:
                    new_addr = Address(
                        address=addr,
                        label=label,
                        address_type=type_,
                        risk_score=95 if risk in ["High", "Critical"] else 10,
                        case_id=None # Global intel, not specific to a case initially
                    )
                    db.add(new_addr)
            db.commit()
            print("[+] Threat Intel DB Seeded")
        except Exception as e:
            print(f"[-] seeding failed or already done: {e}")
        finally:
            db.close()

    def lookup_address(self, address):
        """Check local DB and (Mock) External API"""
        db = SessionLocal()
        try:
            # 1. Local DB Check
            match = db.query(Address).filter_by(address=address).first()
            if match and match.label:
                return {
                    "source": "Local Intelligence",
                    "entity": match.label,
                    "type": match.address_type,
                    "risk": match.risk_score
                }
            
            # 2. Mock External API (e.g., CryptoscamDB)
            # In production, use requests.get('https://api.cryptoscamdb.org/v1/check/' + address)
            return None
        finally:
            db.close()

# Global Instance
threat_intel = ThreatIntel()
