"""
DEX/DeFi Integration Module
Track activity on Uniswap, Aave, Curve, and other DeFi protocols
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class DeFiAnalyzer:
    """
    Track DeFi activities:
    - Uniswap swaps and liquidity positions
    - Aave borrowing/lending
    - Curve pool activities
    - Yield farming
    - LP positions
    """
    
    # GraphQL endpoints for The Graph
    UNISWAP_GRAPH = os.getenv(
        'UNISWAP_GRAPH_URL',
        'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
    )
    
    AAVE_GRAPH = os.getenv(
        'AAVE_GRAPH_URL',
        'https://api.thegraph.com/subgraphs/name/aave/protocol-v3'
    )
    
    CURVE_GRAPH = 'https://api.thegraph.com/subgraphs/name/convex-community/curve-pools'
    
    def __init__(self):
        self.headers = {'Content-Type': 'application/json'}
    
    # ==================== UNISWAP V3 ====================
    
    def get_uniswap_swaps(self, address: str, limit: int = 100) -> List[Dict]:
        """Get Uniswap V3 swaps by address"""
        
        query = """
        {
            swaps(
                first: %d
                where: { origin: "%s" }
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                timestamp
                origin
                amount0
                amount1
                amountUSD
                token0 { symbol }
                token1 { symbol }
                pool { 
                    id 
                    feeTier
                }
            }
        }
        """ % (limit, address.lower())
        
        try:
            response = requests.post(
                self.UNISWAP_GRAPH,
                json={'query': query},
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            
            if 'data' in data:
                swaps = data['data'].get('swaps', [])
                return [self._parse_uniswap_swap(swap) for swap in swaps]
        except Exception as e:
            print(f"Error fetching Uniswap swaps: {str(e)}")
        
        return []
    
    def _parse_uniswap_swap(self, swap: Dict) -> Dict:
        """Parse Uniswap swap data"""
        return {
            'type': 'uniswap_swap',
            'tx_hash': swap['id'].split('-')[0] if '-' in swap['id'] else swap['id'],
            'timestamp': int(swap['timestamp']),
            'address': swap['origin'],
            
            'token_in': swap['token0']['symbol'],
            'amount_in': float(swap['amount0']),
            'token_out': swap['token1']['symbol'],
            'amount_out': float(swap['amount1']),
            
            'usd_value': float(swap['amountUSD']),
            'pool': swap['pool']['id'],
            'fee_tier': swap['pool']['feeTier'],
            
            'processed_at': datetime.utcnow().isoformat()
        }
    
    def get_uniswap_positions(self, address: str) -> List[Dict]:
        """Get active Uniswap V3 liquidity positions"""
        
        query = """
        {
            positions(
                where: { owner: "%s", liquidity_gt: "0" }
                first: 100
            ) {
                id
                owner
                pool { 
                    id
                    token0 { symbol }
                    token1 { symbol }
                    feeTier
                }
                tickLower
                tickUpper
                liquidity
                depositedToken0
                depositedToken1
                withdrawnToken0
                withdrawnToken1
                collectedFeesToken0
                collectedFeesToken1
            }
        }
        """ % address.lower()
        
        try:
            response = requests.post(
                self.UNISWAP_GRAPH,
                json={'query': query},
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            
            if 'data' in data:
                positions = data['data'].get('positions', [])
                return [self._parse_uniswap_position(pos) for pos in positions]
        except Exception as e:
            print(f"Error fetching Uniswap positions: {str(e)}")
        
        return []
    
    def _parse_uniswap_position(self, position: Dict) -> Dict:
        """Parse Uniswap LP position"""
        return {
            'type': 'uniswap_lp',
            'position_id': position['id'],
            'owner': position['owner'],
            
            'pool': position['pool']['id'],
            'token_0': position['pool']['token0']['symbol'],
            'token_1': position['pool']['token1']['symbol'],
            'fee_tier': position['pool']['feeTier'],
            
            'liquidity': float(position['liquidity']),
            'tick_lower': int(position['tickLower']),
            'tick_upper': int(position['tickUpper']),
            
            'deposited_token_0': float(position['depositedToken0']),
            'deposited_token_1': float(position['depositedToken1']),
            
            'fees_collected_0': float(position['collectedFeesToken0']),
            'fees_collected_1': float(position['collectedFeesToken1']),
            
            'last_checked': datetime.utcnow().isoformat()
        }
    
    # ==================== AAVE ====================
    
    def get_aave_user_data(self, address: str) -> Dict:
        """Get Aave user's lending/borrowing data"""
        
        query = """
        {
            users(where: { id: "%s" }) {
                id
                borrowedReservesCount
                unclaimedRewardsUSD
                supplies {
                    reserve {
                        symbol
                        decimals
                    }
                    amount
                }
                borrows {
                    reserve {
                        symbol
                        decimals
                    }
                    amount
                }
            }
        }
        """ % address.lower()
        
        try:
            response = requests.post(
                self.AAVE_GRAPH,
                json={'query': query},
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            
            if 'data' in data and data['data'].get('users'):
                user = data['data']['users'][0]
                return self._parse_aave_user(user)
        except Exception as e:
            print(f"Error fetching Aave data: {str(e)}")
        
        return {}
    
    def _parse_aave_user(self, user: Dict) -> Dict:
        """Parse Aave user data"""
        return {
            'type': 'aave_user',
            'address': user['id'],
            
            'supplies': [{
                'token': s['reserve']['symbol'],
                'amount': float(s['amount']) / (10 ** int(s['reserve']['decimals']))
            } for s in user.get('supplies', [])],
            
            'borrows': [{
                'token': b['reserve']['symbol'],
                'amount': float(b['amount']) / (10 ** int(b['reserve']['decimals']))
            } for b in user.get('borrows', [])],
            
            'borrowed_assets_count': int(user['borrowedReservesCount']),
            'unclaimed_rewards_usd': float(user.get('unclaimedRewardsUSD', 0)),
            
            'activity_type': 'lender' if user.get('supplies') and not user.get('borrows') 
                            else 'borrower' if user.get('borrows') and not user.get('supplies')
                            else 'lender_borrower' if user.get('supplies') and user.get('borrows')
                            else 'inactive',
            
            'checked_at': datetime.utcnow().isoformat()
        }
    
    # ==================== CURVE ====================
    
    def get_curve_pool_activity(self, pool_address: str) -> Dict:
        """Get activity in Curve pool"""
        
        query = """
        {
            pools(where: { id: "%s" }) {
                id
                name
                tokens { symbol }
                exchanges(orderBy: timestamp, orderDirection: desc, first: 100) {
                    id
                    timestamp
                    buyer
                    tokens { symbol }
                    amounts
                }
            }
        }
        """ % pool_address.lower()
        
        try:
            response = requests.post(
                self.CURVE_GRAPH,
                json={'query': query},
                headers=self.headers,
                timeout=10
            )
            data = response.json()
            
            if 'data' in data and data['data'].get('pools'):
                pool = data['data']['pools'][0]
                return self._parse_curve_pool(pool)
        except Exception as e:
            print(f"Error fetching Curve data: {str(e)}")
        
        return {}
    
    def _parse_curve_pool(self, pool: Dict) -> Dict:
        """Parse Curve pool data"""
        return {
            'type': 'curve_pool',
            'pool_id': pool['id'],
            'name': pool['name'],
            'tokens': [t['symbol'] for t in pool['tokens']],
            
            'recent_exchanges': [{
                'timestamp': int(ex['timestamp']),
                'buyer': ex['buyer'],
                'amounts': [float(a) for a in ex['amounts']],
                'tokens': [t['symbol'] for t in ex['tokens']]
            } for ex in pool.get('exchanges', [])],
            
            'last_updated': datetime.utcnow().isoformat()
        }
    
    # ==================== CONSOLIDATED ANALYSIS ====================
    
    def analyze_defi_activity(self, address: str) -> Dict:
        """
        Consolidated DeFi activity analysis
        Shows all DeFi interactions
        """
        
        analysis = {
            'address': address,
            'defi_activity': {
                'uniswap': {
                    'swaps': [],
                    'positions': [],
                    'is_lp': False,
                    'is_trader': False
                },
                'aave': {},
                'curve': [],
            },
            'activity_summary': {
                'protocols_used': [],
                'total_swaps': 0,
                'active_lp_positions': 0,
                'borrowed_assets': 0,
                'lending_activity': False,
                'risk_assessment': 'LOW'
            },
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        # Uniswap V3
        print(f"[DeFi] Fetching Uniswap data for {address}...")
        swaps = self.get_uniswap_swaps(address)
        positions = self.get_uniswap_positions(address)
        
        if swaps:
            analysis['defi_activity']['uniswap']['swaps'] = swaps
            analysis['activity_summary']['is_trader'] = True
            analysis['activity_summary']['total_swaps'] = len(swaps)
        
        if positions:
            analysis['defi_activity']['uniswap']['positions'] = positions
            analysis['activity_summary']['is_lp'] = True
            analysis['activity_summary']['active_lp_positions'] = len(positions)
        
        if swaps or positions:
            analysis['activity_summary']['protocols_used'].append('Uniswap V3')
        
        # Aave
        print(f"[DeFi] Fetching Aave data for {address}...")
        aave_data = self.get_aave_user_data(address)
        if aave_data:
            analysis['defi_activity']['aave'] = aave_data
            analysis['activity_summary']['protocols_used'].append('Aave')
            analysis['activity_summary']['lending_activity'] = True
            
            if aave_data.get('activity_type') in ['borrower', 'lender_borrower']:
                analysis['activity_summary']['borrowed_assets'] = len(aave_data.get('borrows', []))
        
        # Risk assessment based on DeFi activity
        risk_score = self._assess_defi_risk(analysis)
        analysis['activity_summary']['risk_assessment'] = self._risk_score_to_level(risk_score)
        
        return analysis
    
    def _assess_defi_risk(self, analysis: Dict) -> float:
        """Assess risk from DeFi activities"""
        risk = 0
        
        if analysis['activity_summary']['total_swaps'] > 100:
            risk += 10
        
        if analysis['activity_summary']['borrowed_assets'] > 5:
            risk += 15
        
        if 'Aave' in analysis['activity_summary']['protocols_used']:
            risk -= 5  # Known protocol reduces risk
        
        return min(100, max(0, risk))
    
    def _risk_score_to_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score >= 75:
            return 'HIGH'
        elif score >= 50:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def detect_yield_farming(self, address: str) -> List[Dict]:
        """Detect yield farming activities (repeated deposits/withdrawals)"""
        
        positions = self.get_uniswap_positions(address)
        yield_farms = []
        
        for pos in positions:
            # Check if frequently collecting fees (signs of active yield farming)
            if pos['fees_collected_0'] > 0 or pos['fees_collected_1'] > 0:
                yield_farms.append({
                    'type': 'uniswap_yield',
                    'position_id': pos['position_id'],
                    'tokens': f"{pos['token_0']}/{pos['token_1']}",
                    'fees_earned_0': pos['fees_collected_0'],
                    'fees_earned_1': pos['fees_collected_1'],
                    'apy_estimate': self._estimate_apy(pos)
                })
        
        return yield_farms
    
    def _estimate_apy(self, position: Dict) -> Optional[float]:
        """
        Rough estimate of APY for LP position
        In real implementation, would need more data
        """
        total_deposited = position['deposited_token_0'] + position['deposited_token_1']
        total_fees = position['fees_collected_0'] + position['fees_collected_1']
        
        if total_deposited > 0:
            return (total_fees / total_deposited) * 100
        return None


def test_defi_analyzer():
    """Test DeFi analyzer"""
    analyzer = DeFiAnalyzer()
    
    # Example: Vitalik Buterin
    result = analyzer.analyze_defi_activity('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    test_defi_analyzer()
