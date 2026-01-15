"""
Case Management System for OPENCHAIN IR
Handles case creation, address tagging, and investigation notes
"""

import json
import os
from datetime import datetime
from pathlib import Path

CASES_DIR = "cases"

class Case:
    """Represents a single investigation case"""
    
    def __init__(self, case_id, name, description="", investigator=""):
        self.case_id = case_id
        self.name = name
        self.description = description
        self.investigator = investigator
        self.created_at = datetime.now().isoformat()
        self.addresses = {}  # {address: {tag, notes, risk_level, status}}
        self.findings = []
        self.timeline = []
        
    def add_address(self, address, tag="suspect", notes="", risk_level=0):
        """Add address to case with metadata"""
        self.addresses[address.lower()] = {
            "tag": tag,  # victim, suspect, intermediary, exchange
            "notes": notes,
            "risk_level": risk_level,
            "status": "active",
            "added_at": datetime.now().isoformat()
        }
        
    def add_note(self, content, address=None):
        """Add investigation note"""
        self.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "type": "note",
            "content": content,
            "address": address
        })
        
    def add_finding(self, finding):
        """Add key finding to case"""
        self.findings.append({
            "timestamp": datetime.now().isoformat(),
            "finding": finding
        })
        
    def to_dict(self):
        """Convert case to dictionary"""
        return {
            "case_id": self.case_id,
            "name": self.name,
            "description": self.description,
            "investigator": self.investigator,
            "created_at": self.created_at,
            "addresses": self.addresses,
            "findings": self.findings,
            "timeline": self.timeline
        }
    
    @staticmethod
    def from_dict(data):
        """Create case from dictionary"""
        case = Case(data["case_id"], data["name"], 
                data.get("description", ""), 
                data.get("investigator", ""))
        case.created_at = data.get("created_at")
        case.addresses = data.get("addresses", {})
        case.findings = data.get("findings", [])
        case.timeline = data.get("timeline", [])
        return case


class CaseManager:
    """Manages multiple cases"""
    
    def __init__(self):
        self.cases = {}
        self.load_all_cases()
        
    def create_case(self, name, description="", investigator=""):
        """Create new case"""
        case_id = f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        case = Case(case_id, name, description, investigator)
        self.cases[case_id] = case
        self.save_case(case)
        return case
    
    def get_case(self, case_id):
        """Get case by ID"""
        return self.cases.get(case_id)
    
    def list_cases(self):
        """List all cases"""
        return list(self.cases.values())
    
    def add_address_to_case(self, case_id, address, tag="suspect", notes="", risk_level=0):
        """Add address to existing case"""
        case = self.get_case(case_id)
        if case:
            case.add_address(address, tag, notes, risk_level)
            self.save_case(case)
            return True
        return False
    
    def add_note_to_case(self, case_id, content, address=None):
        """Add note to case"""
        case = self.get_case(case_id)
        if case:
            case.add_note(content, address)
            self.save_case(case)
            return True
        return False
    
    def save_case(self, case):
        """Save case to file"""
        os.makedirs(CASES_DIR, exist_ok=True)
        filepath = os.path.join(CASES_DIR, f"{case.case_id}.json")
        with open(filepath, "w") as f:
            json.dump(case.to_dict(), f, indent=2)
    
    def load_all_cases(self):
        """Load all cases from files"""
        if not os.path.exists(CASES_DIR):
            return
        
        for filename in os.listdir(CASES_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(CASES_DIR, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        case = Case.from_dict(data)
                        self.cases[case.case_id] = case
                except Exception as e:
                    print(f"[ERROR] Loading case {filename}: {e}")
    
    def get_case_summary(self, case_id):
        """Get case summary for reports"""
        case = self.get_case(case_id)
        if not case:
            return None
        
        return {
            "case_id": case.case_id,
            "name": case.name,
            "investigator": case.investigator,
            "address_count": len(case.addresses),
            "finding_count": len(case.findings),
            "created_at": case.created_at,
            "addresses": case.addresses,
            "findings": case.findings[:5],  # Last 5 findings
            "timeline_count": len(case.timeline)
        }
