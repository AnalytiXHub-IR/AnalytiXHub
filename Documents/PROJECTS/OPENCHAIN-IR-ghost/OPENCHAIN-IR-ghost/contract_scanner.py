
import re

class ContractScanner:
    def __init__(self):
        # Known malicious signatures (simplified/conceptual)
        self.signatures = {
            "Honeypot (Transfer Disable)": r"require\s*\(\s*!_blacklisted\[",
            "Hidden Mint": r"function\s+mint\s*\(.*onlyOwner",
            "Rug Pull (Liquidity Drain)": r"function\s+removeLiquidity\s*\(.*public",
            "Self Destruct": r"selfdestruct\s*\(",
            "Delegate Call (Unsafe)": r"delegatecall\s*\("
        }

    def scan_source_code(self, source_code):
        """Scan Solidity source code for risk patterns"""
        findings = []
        risk_score = 0
        
        for name, pattern in self.signatures.items():
            if re.search(pattern, source_code, re.IGNORECASE):
                findings.append(name)
                risk_score += 20
                
        # Heuristics
        if "onlyOwner" in source_code and "withdraw" in source_code:
            findings.append("Owner Withdrawal Logic Detected")
            risk_score += 10
            
        return {
            "risk_score": min(risk_score, 100),
            "findings": findings,
            "is_verified": True # Mock
        }

    def scan_bytecode(self, bytecode):
        """Scan compiled bytecode for opcodes (Mock/Simulated)"""
        # In a real tool, we'd use evm-disassembler
        findings = []
        # Check for SELFDESTRUCT opcode (0xff)
        if "ff" in bytecode[-10:]: # Very naive check
            findings.append("Potential Self-Destruct")
            
        return {
            "risk_score": 10 if findings else 0,
            "findings": findings
        }

# Global Instance
contract_scanner = ContractScanner()
