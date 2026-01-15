"""
Smart Contract Analysis Module
Detect vulnerabilities, rug pulls, and honeypots
"""

import requests
import json
import re
from typing import Dict, List, Tuple
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class SmartContractAnalyzer:
    """
    Analyze Ethereum/EVM smart contracts for:
    - Security vulnerabilities
    - Rug pull patterns
    - Honeypot detection
    - Suspicious function behavior
    """
    
    def __init__(self, etherscan_api_key: str = None):
        self.api_key = etherscan_api_key or os.getenv('ETHERSCAN_API_KEY')
        self.base_url = 'https://api.etherscan.io/api'
        
        # Common vulnerability patterns
        self.rug_pull_patterns = [
            'selfdestruct',
            'pause',
            'blacklist',
            'freeze',
            'mint_unlimited',
            'no_liquidity_lock'
        ]
        
        self.honeypot_patterns = [
            'onlyowner_buy',
            'onlyowner_sell',
            'custom_transfer_restrictions',
            'hidden_fees',
            'sell_ban'
        ]
    
    def get_contract_source(self, contract_address: str, chain: str = 'ethereum') -> Dict:
        """Fetch contract source code from Etherscan"""
        
        params = {
            'action': 'getsourcecode',
            'address': contract_address,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                return {
                    'success': True,
                    'address': contract_address,
                    'source_code': data['result'][0]['SourceCode'],
                    'contract_name': data['result'][0]['ContractName'],
                    'compiler_version': data['result'][0]['CompilerVersion'],
                    'abi': data['result'][0].get('ABI'),
                    'is_verified': True
                }
        except Exception as e:
            print(f"Error fetching contract source: {str(e)}")
        
        return {
            'success': False,
            'address': contract_address,
            'is_verified': False,
            'error': 'Contract source not available or not verified'
        }
    
    def detect_rug_pull_indicators(self, source_code: str, abi: str = None) -> Dict:
        """
        Detect common rug pull patterns in contract code
        
        Patterns:
        1. Selfdestruct in contract
        2. Owner can drain liquidity
        3. Owner can pause/freeze transfers
        4. Unlimited minting capability
        5. No liquidity lock
        """
        
        indicators = {
            'risk_score': 0,
            'patterns_found': [],
            'severity': 'LOW',
            'confidence': 0
        }
        
        # Check for selfdestruct
        if 'selfdestruct' in source_code.lower():
            indicators['patterns_found'].append({
                'pattern': 'SELFDESTRUCT',
                'description': 'Contract can self-destruct (owner can drain)',
                'risk': 'CRITICAL'
            })
            indicators['risk_score'] += 30
        
        # Check for unlimited minting
        if re.search(r'function\s+mint\s*\(.*\)\s*(public|external)(?!.*onlyOwner)', source_code, re.IGNORECASE):
            indicators['patterns_found'].append({
                'pattern': 'UNLIMITED_MINT',
                'description': 'Anyone can mint tokens (infinite supply)',
                'risk': 'CRITICAL'
            })
            indicators['risk_score'] += 25
        
        # Check for owner pause function
        if re.search(r'(pause|freeze|stop).*transfer', source_code, re.IGNORECASE):
            indicators['patterns_found'].append({
                'pattern': 'PAUSE_TRANSFER',
                'description': 'Owner can pause/freeze token transfers',
                'risk': 'HIGH'
            })
            indicators['risk_score'] += 20
        
        # Check for blacklist/whitelist
        if re.search(r'(blacklist|whitelist|banned)', source_code, re.IGNORECASE):
            indicators['patterns_found'].append({
                'pattern': 'BLACKLIST',
                'description': 'Blacklist/whitelist functionality (can freeze addresses)',
                'risk': 'MEDIUM'
            })
            indicators['risk_score'] += 15
        
        # Check for hidden transfer logic
        if '_transfer' in source_code and 'require' not in source_code.split('_transfer')[1][:200]:
            indicators['patterns_found'].append({
                'pattern': 'HIDDEN_TRANSFER_LOGIC',
                'description': 'Custom transfer logic without restrictions',
                'risk': 'HIGH'
            })
            indicators['risk_score'] += 15
        
        # Check for emergency withdrawal
        if re.search(r'(withdrawAll|emergencyWithdraw|drainBalance)', source_code, re.IGNORECASE):
            indicators['patterns_found'].append({
                'pattern': 'EMERGENCY_WITHDRAW',
                'description': 'Emergency withdrawal function (can drain liquidity)',
                'risk': 'CRITICAL'
            })
            indicators['risk_score'] += 20
        
        indicators['risk_score'] = min(100, indicators['risk_score'])
        
        if indicators['risk_score'] >= 75:
            indicators['severity'] = 'CRITICAL'
            indicators['confidence'] = 0.95
        elif indicators['risk_score'] >= 50:
            indicators['severity'] = 'HIGH'
            indicators['confidence'] = 0.85
        elif indicators['risk_score'] >= 25:
            indicators['severity'] = 'MEDIUM'
            indicators['confidence'] = 0.7
        else:
            indicators['severity'] = 'LOW'
            indicators['confidence'] = 0.5
        
        return indicators
    
    def detect_honeypot(self, source_code: str, abi: str = None) -> Dict:
        """
        Detect honeypot patterns
        
        Signs:
        1. Owner can sell but users can't
        2. Massive buy fee, no sell fee
        3. Hidden transfer restrictions
        4. Sell limit per address
        """
        
        honeypot_indicators = {
            'is_honeypot': False,
            'risk_score': 0,
            'patterns': [],
            'confidence': 0
        }
        
        # Check for asymmetric buy/sell permissions
        if re.search(r'(onlyOwner.*buy|buy.*onlyOwner)', source_code, re.IGNORECASE):
            honeypot_indicators['patterns'].append({
                'pattern': 'OWNER_ONLY_BUY',
                'description': 'Only owner can buy tokens',
                'risk': 'CRITICAL'
            })
            honeypot_indicators['risk_score'] += 35
        
        # Check for no-sell pattern
        if re.search(r'(cannot.*sell|sell.*forbidden|sell.*disabled)', source_code, re.IGNORECASE):
            honeypot_indicators['patterns'].append({
                'pattern': 'SELL_DISABLED',
                'description': 'Token transfers/sales are disabled',
                'risk': 'CRITICAL'
            })
            honeypot_indicators['risk_score'] += 35
        
        # Check for massive buy fee
        fee_pattern = re.search(r'(buyFee|buy_fee)\s*=\s*(\d+)', source_code, re.IGNORECASE)
        if fee_pattern and int(fee_pattern.group(2)) > 20:
            honeypot_indicators['patterns'].append({
                'pattern': 'MASSIVE_BUY_FEE',
                'description': f'Very high buy fee ({fee_pattern.group(2)}%)',
                'risk': 'HIGH'
            })
            honeypot_indicators['risk_score'] += 25
        
        # Check for per-address sell limit
        if re.search(r'(sellLimit|maxSell|maxSellAmount)', source_code, re.IGNORECASE):
            honeypot_indicators['patterns'].append({
                'pattern': 'SELL_LIMIT',
                'description': 'Per-address sell limit enforced',
                'risk': 'HIGH'
            })
            honeypot_indicators['risk_score'] += 20
        
        # Check for revert on sell
        if re.search(r'require.*sell.*false', source_code, re.IGNORECASE):
            honeypot_indicators['patterns'].append({
                'pattern': 'REVERT_ON_SELL',
                'description': 'Sales revert (trapped tokens)',
                'risk': 'CRITICAL'
            })
            honeypot_indicators['risk_score'] += 40
        
        honeypot_indicators['risk_score'] = min(100, honeypot_indicators['risk_score'])
        
        if honeypot_indicators['risk_score'] >= 60:
            honeypot_indicators['is_honeypot'] = True
            honeypot_indicators['confidence'] = 0.9
        elif honeypot_indicators['risk_score'] >= 30:
            honeypot_indicators['confidence'] = 0.65
        else:
            honeypot_indicators['confidence'] = 0.4
        
        return honeypot_indicators
    
    def check_liquidity_lock(self, source_code: str) -> Dict:
        """Check if liquidity is locked or can be withdrawn"""
        
        lock_info = {
            'has_liquidity_lock': False,
            'lock_duration': None,
            'lock_patterns': [],
            'risk': 'UNKNOWN'
        }
        
        # Check for common lock mechanisms
        if 'uniswapV2Pair' in source_code:
            lock_info['lock_patterns'].append('Uniswap V2 LP token detected')
        
        # Check for lock time
        lock_time = re.search(r'lockTime\s*=\s*(\d+)', source_code)
        if lock_time:
            lock_info['has_liquidity_lock'] = True
            lock_info['lock_duration'] = int(lock_time.group(1))
            lock_info['lock_patterns'].append(f'Lock duration: {lock_time.group(1)} seconds')
        
        # Check for lock contract reference
        if re.search(r'(Locker|Lock|LockManager)', source_code):
            lock_info['has_liquidity_lock'] = True
            lock_info['lock_patterns'].append('Uses external lock contract')
        
        # Check for explicit removal warning
        if 'cannot remove liquidity' in source_code.lower():
            lock_info['has_liquidity_lock'] = True
            lock_info['lock_patterns'].append('Explicit: Cannot remove liquidity')
        
        if lock_info['has_liquidity_lock']:
            lock_info['risk'] = 'LOW'
        else:
            lock_info['risk'] = 'HIGH'
            lock_info['lock_patterns'].append('⚠️  No liquidity lock detected - high rug pull risk')
        
        return lock_info
    
    def analyze_contract(self, contract_address: str, chain: str = 'ethereum') -> Dict:
        """
        Comprehensive contract analysis
        Returns all findings and risk assessment
        """
        
        # Fetch source code
        source_info = self.get_contract_source(contract_address, chain)
        
        if not source_info['success']:
            return {
                'address': contract_address,
                'is_verified': False,
                'error': 'Contract source not available',
                'risk_level': 'UNKNOWN'
            }
        
        source_code = source_info.get('source_code', '')
        abi = source_info.get('abi')
        
        # Run all analysis
        rug_pull = self.detect_rug_pull_indicators(source_code, abi)
        honeypot = self.detect_honeypot(source_code, abi)
        liquidity_lock = self.check_liquidity_lock(source_code)
        
        # Calculate overall risk
        overall_risk = (rug_pull['risk_score'] * 0.4 + 
                       honeypot['risk_score'] * 0.3 + 
                       (0 if liquidity_lock['has_liquidity_lock'] else 40) * 0.3)
        
        overall_risk = min(100, overall_risk)
        
        return {
            'address': contract_address,
            'name': source_info['contract_name'],
            'is_verified': True,
            'compiler_version': source_info['compiler_version'],
            
            'rug_pull_analysis': rug_pull,
            'honeypot_analysis': honeypot,
            'liquidity_lock_analysis': liquidity_lock,
            
            'overall_risk_score': overall_risk,
            'overall_risk_level': (
                'CRITICAL' if overall_risk >= 75 else
                'HIGH' if overall_risk >= 50 else
                'MEDIUM' if overall_risk >= 25 else
                'LOW'
            ),
            
            'recommendation': self._get_recommendation(overall_risk, rug_pull, honeypot),
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def _get_recommendation(self, overall_risk: float, rug_pull: Dict, honeypot: Dict) -> str:
        """Generate recommendation based on analysis"""
        
        if overall_risk >= 80:
            return "🚫 AVOID - High probability of scam/rug pull. Do not invest."
        elif overall_risk >= 60:
            return "⚠️  EXTREME CAUTION - Multiple suspicious patterns detected. High risk."
        elif overall_risk >= 40:
            return "⚠️  CAUTION - Some suspicious patterns found. Verify before investing."
        elif overall_risk >= 20:
            return "⚠️  REVIEW - Minor concerns. Research team and liquidity status."
        else:
            return "✓ LOW RISK - No major red flags detected. Still conduct due diligence."


# Quick test functions
def test_contract_analysis():
    """Test smart contract analyzer"""
    analyzer = SmartContractAnalyzer()
    
    # Example: Uniswap V3 Router (legitimate)
    result = analyzer.analyze_contract('0xE592427A0AEce92De3Edee1F18E0157C05861564')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    test_contract_analysis()
