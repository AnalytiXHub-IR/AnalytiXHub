"""
Threat Intelligence Integration Module
Connect to known scam databases, OFAC lists, and sanctions data
"""

import requests
import json
from typing import List, Dict, Optional, Set
from datetime import datetime
import csv
from io import StringIO
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

class ThreatIntelligenceAPI:
    """
    Threat Intelligence aggregator
    Sources:
    - OFAC (US Treasury) - Sanctioned entities
    - Etherscan Phishing List - Known scam addresses
    - SlowMist EvilList - Known malicious addresses
    - Internal threat database
    """
    
    # Free data sources
    ETHERSCAN_PHISHING = 'https://phishing-filter.badger.com/v1/phishingFilter'
    SLOWMIST_EVILLIST = 'https://raw.githubusercontent.com/slowmist/SlowMistData/master/eviladdresses/addresses.csv'
    OFAC_URL = 'https://www.treasury.gov/ofac'
    
    def __init__(self):
        self.threat_cache = {}
        self.ofac_list = set()
        self.phishing_list = set()
        self.evil_addresses = set()
        
        # Load threat data on init
        self._load_threat_data()
    
    def _load_threat_data(self):
        """Load all threat intelligence data sources"""
        print("[TI] Loading threat intelligence data...")
        
        # Load OFAC list
        self.ofac_list = self._fetch_ofac_list()
        print(f"  ✓ OFAC: {len(self.ofac_list)} sanctioned addresses")
        
        # Load Etherscan phishing
        self.phishing_list = self._fetch_etherscan_phishing()
        print(f"  ✓ Etherscan Phishing: {len(self.phishing_list)} addresses")
        
        # Load SlowMist evil addresses
        self.evil_addresses = self._fetch_slowmist_evil()
        print(f"  ✓ SlowMist: {len(self.evil_addresses)} malicious addresses")
    
    def _fetch_ofac_list(self) -> Set[str]:
        """Fetch OFAC (Office of Foreign Assets Control) sanctioned list"""
        sanctioned = set()
        
        try:
            # OFAC SDN (Specially Designated Nationals) list
            # For production: Download from https://www.treasury.gov/resource-center/sanctions/sdn-list
            # For now, use known sanctioned crypto addresses
            
            known_sanctioned = {
                '0x59a92b5660f7a1ce51a9ee8f0d0c89d9a86f5a78',  # Lazarus Group
                '0x2f389ce8bd8ff92de3402ffaf84de0baadfc4755',  # North Korea
                '0x60f380bad5ed1632429e5ec7d748c46d1d7db5b9',  # Iran connected
            }
            
            sanctioned.update(known_sanctioned)
            
        except Exception as e:
            print(f"Warning: Could not fetch OFAC list: {str(e)}")
        
        return sanctioned
    
    def _fetch_etherscan_phishing(self) -> Set[str]:
        """Fetch known phishing/scam addresses"""
        phishing = set()
        
        try:
            response = requests.get(self.ETHERSCAN_PHISHING, timeout=10)
            if response.status_code == 200:
                # Etherscan provides a filter list
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('0x'):
                        phishing.add(line.lower())
        except Exception as e:
            print(f"Warning: Could not fetch Etherscan phishing list: {str(e)}")
        
        return phishing
    
    def _fetch_slowmist_evil(self) -> Set[str]:
        """Fetch SlowMist blacklist of malicious addresses"""
        evil = set()
        
        try:
            response = requests.get(self.SLOWMIST_EVILLIST, timeout=10)
            if response.status_code == 200:
                csv_data = csv.DictReader(StringIO(response.text))
                for row in csv_data:
                    if 'address' in row:
                        evil.add(row['address'].lower())
        except Exception as e:
            print(f"Warning: Could not fetch SlowMist list: {str(e)}")
        
        return evil
    
    def check_address(self, address: str) -> Dict:
        """
        Check single address against all threat databases
        Returns threat info if found
        """
        address_lower = address.lower()
        
        threat_info = {
            'address': address,
            'is_flagged': False,
            'threat_type': None,
            'sources': [],
            'severity': 'UNKNOWN',
            'confidence': 0,
            'details': {}
        }
        
        # Check OFAC
        if address_lower in self.ofac_list:
            threat_info['is_flagged'] = True
            threat_info['threat_type'] = 'sanctioned_entity'
            threat_info['sources'].append('OFAC')
            threat_info['severity'] = 'CRITICAL'
            threat_info['confidence'] = 1.0
            threat_info['details']['ofac'] = 'Listed in OFAC SDN list'
        
        # Check Phishing List
        if address_lower in self.phishing_list:
            threat_info['is_flagged'] = True
            threat_info['threat_type'] = 'phishing_scam'
            threat_info['sources'].append('Etherscan_Phishing')
            threat_info['severity'] = 'HIGH'
            threat_info['confidence'] = 0.95
            threat_info['details']['phishing'] = 'Known phishing/scam address'
        
        # Check SlowMist Evil List
        if address_lower in self.evil_addresses:
            threat_info['is_flagged'] = True
            threat_info['threat_type'] = 'malicious'
            threat_info['sources'].append('SlowMist')
            threat_info['severity'] = 'CRITICAL'
            threat_info['confidence'] = 0.90
            threat_info['details']['slowmist'] = 'Listed as malicious by SlowMist'
        
        # Set overall severity if flagged
        if threat_info['is_flagged']:
            if 'CRITICAL' in threat_info['sources']:
                threat_info['severity'] = 'CRITICAL'
            elif 'HIGH' in threat_info['sources']:
                threat_info['severity'] = 'HIGH'
        
        threat_info['checked_at'] = datetime.utcnow().isoformat()
        
        return threat_info
    
    def bulk_check(self, addresses: List[str]) -> Dict[str, Dict]:
        """Check multiple addresses at once"""
        results = {}
        flagged = []
        
        for addr in addresses:
            result = self.check_address(addr)
            results[addr] = result
            
            if result['is_flagged']:
                flagged.append(result)
        
        return {
            'total_checked': len(addresses),
            'total_flagged': len(flagged),
            'flagged_addresses': flagged,
            'results': results
        }
    
    def get_threat_summary(self, addresses: List[str]) -> Dict:
        """Get summary of threats in address list"""
        check_results = self.bulk_check(addresses)
        
        threat_types = {}
        severity_distribution = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}
        sources_hit = set()
        
        for addr_result in check_results['results'].values():
            if addr_result['is_flagged']:
                # Count by type
                threat_type = addr_result.get('threat_type', 'unknown')
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
                
                # Count by severity
                severity = addr_result.get('severity', 'UNKNOWN')
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
                
                # Track sources
                for source in addr_result.get('sources', []):
                    sources_hit.add(source)
        
        return {
            'summary': {
                'total_addresses': len(addresses),
                'flagged_count': check_results['total_flagged'],
                'risk_percentage': (check_results['total_flagged'] / len(addresses) * 100) if addresses else 0,
                'severity_distribution': severity_distribution,
                'threat_types_found': threat_types,
                'sources_triggered': list(sources_hit),
            },
            'flagged_addresses': check_results['flagged_addresses'],
            'checked_at': datetime.utcnow().isoformat()
        }


class BlockchainIntelligence:
    """
    Additional intelligence gathering for addresses
    - Known entity identification
    - Behavioral analysis
    - Pattern matching
    """
    
    KNOWN_ENTITIES = {
        # Exchanges
        '0x28c6c06298d514db089934071355e5743bf21d60': {
            'name': 'Binance: Deposit Address',
            'type': 'exchange',
            'trust_level': 'HIGH'
        },
        '0x77696bb39917c91a0c3908d577d5e322095425ca': {
            'name': 'Coinbase: Deposit Address',
            'type': 'exchange',
            'trust_level': 'HIGH'
        },
        
        # Pools & Routers
        '0x1f98431c8ad98523631ae4a59f267346ea31f984': {
            'name': 'Uniswap V3: Factory',
            'type': 'defi_core',
            'trust_level': 'HIGHEST'
        },
        '0x68b3465833fb72b5a828cced3294e3b6b3214313': {
            'name': 'Uniswap V3: Router',
            'type': 'defi_core',
            'trust_level': 'HIGHEST'
        },
        
        # Individuals
        '0xd8da6bf26964af9d7eed9e03e53415d37aa96045': {
            'name': 'Vitalik Buterin',
            'type': 'individual',
            'trust_level': 'HIGHEST'
        },
        
        # Mixers (High Risk)
        '0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc': {
            'name': 'Tornado Cash Router',
            'type': 'mixer',
            'trust_level': 'CRITICAL_RISK'
        },
    }
    
    def identify_entity(self, address: str) -> Dict:
        """Identify known entity"""
        address_lower = address.lower()
        
        if address_lower in self.KNOWN_ENTITIES:
            entity = self.KNOWN_ENTITIES[address_lower].copy()
            entity['address'] = address
            entity['confidence'] = 1.0
            return entity
        
        return {
            'address': address,
            'name': 'Unknown Address',
            'type': 'unknown',
            'trust_level': 'UNKNOWN',
            'confidence': 0
        }
    
    def bulk_identify(self, addresses: List[str]) -> Dict[str, Dict]:
        """Identify multiple addresses"""
        results = {}
        for addr in addresses:
            results[addr] = self.identify_entity(addr)
        return results


def test_threat_intel():
    """Test threat intelligence module"""
    ti = ThreatIntelligenceAPI()
    
    # Test single check
    print("\n[TEST] Single address check:")
    result = ti.check_address('0xd8da6bf26964af9d7eed9e03e53415d37aa96045')
    print(json.dumps(result, indent=2))
    
    # Test bulk check
    print("\n[TEST] Bulk check:")
    addresses = [
        '0xd8da6bf26964af9d7eed9e03e53415d37aa96045',
        '0x28c6c06298d514db089934071355e5743bf21d60',
        '0x1234567890123456789012345678901234567890'
    ]
    summary = ti.get_threat_summary(addresses)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    test_threat_intel()
