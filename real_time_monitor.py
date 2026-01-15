"""
Real-Time Monitoring System
Watch addresses for new transactions, anomalies, and trigger alerts
"""

import asyncio
import time
from typing import List, Dict, Callable, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

# For scheduling
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

# For async operations
try:
    import aiohttp
    import asyncio
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

load_dotenv()

class RealTimeMonitor:
    """
    Monitor addresses in real-time
    - Watch for new transactions
    - Detect anomalies
    - Generate alerts
    - Update dashboards
    """
    
    def __init__(self):
        self.monitored_addresses = {}
        self.alerts = []
        self.transaction_history = defaultdict(list)
        self.anomaly_detector = None
        
        # Configuration
        self.check_interval = int(os.getenv('MONITORING_UPDATE_INTERVAL', 60))  # seconds
        self.max_monitored = int(os.getenv('MONITORING_MAX_ADDRESSES', 10))
        self.alert_threshold_risk = float(os.getenv('ALERT_RISK_THRESHOLD', 0.75))
        self.alert_threshold_anomaly = float(os.getenv('ALERT_ANOMALY_THRESHOLD', 0.8))
        
        # Initialize scheduler if available
        self.scheduler = None
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
    
    def add_address(self, address: str, chain: str = 'ethereum', 
                   alert_on_new_tx: bool = True,
                   alert_on_anomaly: bool = True,
                   alert_on_new_counterparty: bool = False) -> bool:
        """Add address to monitoring"""
        
        if len(self.monitored_addresses) >= self.max_monitored:
            print(f"⚠️  Max monitored addresses ({self.max_monitored}) reached")
            return False
        
        address_lower = address.lower()
        
        self.monitored_addresses[address_lower] = {
            'address': address,
            'chain': chain,
            'added_at': datetime.utcnow(),
            'last_checked': None,
            'last_tx_count': 0,
            'known_counterparties': set(),
            
            # Alert settings
            'alert_on_new_tx': alert_on_new_tx,
            'alert_on_anomaly': alert_on_anomaly,
            'alert_on_new_counterparty': alert_on_new_counterparty,
            
            # Status
            'is_active': True,
            'check_count': 0,
            'anomalies_detected': 0
        }
        
        print(f"✓ Added {address} to monitoring on {chain}")
        return True
    
    def remove_address(self, address: str) -> bool:
        """Remove address from monitoring"""
        address_lower = address.lower()
        if address_lower in self.monitored_addresses:
            del self.monitored_addresses[address_lower]
            print(f"✓ Removed {address} from monitoring")
            return True
        return False
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not SCHEDULER_AVAILABLE:
            print("⚠️  APScheduler not installed. Using polling fallback.")
            self._start_polling()
            return
        
        if not self.scheduler:
            self.scheduler = BackgroundScheduler()
        
        # Add job to check all addresses
        self.scheduler.add_job(
            self.check_all_addresses,
            IntervalTrigger(seconds=self.check_interval),
            id='monitor_addresses',
            name='Monitor all addresses'
        )
        
        if not self.scheduler.running:
            self.scheduler.start()
            print(f"✓ Monitoring started (check every {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            print("✓ Monitoring stopped")
    
    def _start_polling(self):
        """Fallback polling if scheduler not available"""
        print("Starting polling-based monitoring (consider installing APScheduler)")
        # This would be implemented in a separate thread/process
        pass
    
    def check_all_addresses(self):
        """Check all monitored addresses for updates"""
        print(f"\n[Monitor] Checking {len(self.monitored_addresses)} addresses...")
        
        for address, config in self.monitored_addresses.items():
            if config['is_active']:
                self.check_address(address)
        
        print(f"[Monitor] Check complete. Alerts generated: {len(self.alerts)}")
    
    def check_address(self, address: str):
        """Check single address for updates"""
        if address not in self.monitored_addresses:
            return
        
        config = self.monitored_addresses[address]
        
        # Simulate fetching new transaction data
        # In production, use eth_live.fetch_eth_address_with_counts()
        
        new_tx_count = self._get_transaction_count(address)
        config['last_checked'] = datetime.utcnow()
        config['check_count'] += 1
        
        # Check for new transactions
        if new_tx_count > config['last_tx_count']:
            new_txs = new_tx_count - config['last_tx_count']
            
            if config['alert_on_new_tx']:
                self._generate_alert(
                    address=address,
                    alert_type='new_transaction',
                    severity='MEDIUM',
                    description=f"{new_txs} new transaction(s) detected",
                    metadata={'new_tx_count': new_txs}
                )
            
            config['last_tx_count'] = new_tx_count
        
        # Check for anomalies
        self._check_for_anomalies(address)
        
        # Check for new counterparties
        if config['alert_on_new_counterparty']:
            self._check_for_new_counterparties(address)
    
    def _get_transaction_count(self, address: str) -> int:
        """Get current transaction count for address"""
        # In production: call Etherscan API
        # For now, return mock data
        return len(self.transaction_history.get(address, []))
    
    def _check_for_anomalies(self, address: str):
        """Detect anomalous activity"""
        
        # Simple anomaly checks
        anomalies = []
        
        recent_txs = self.transaction_history.get(address, [])[-10:]  # Last 10 txs
        
        if len(recent_txs) >= 5:
            # Check for unusual frequency
            timestamps = [tx['timestamp'] for tx in recent_txs]
            time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            
            avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            
            if avg_time_diff < 30:  # Transactions within 30 seconds
                anomalies.append({
                    'type': 'unusual_frequency',
                    'description': 'Rapid succession of transactions',
                    'severity': 'HIGH'
                })
            
            # Check for unusual amounts
            amounts = [float(tx.get('value', 0)) for tx in recent_txs]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            
            for amount in amounts:
                if amount > avg_amount * 5:
                    anomalies.append({
                        'type': 'unusual_amount',
                        'description': f'Transaction amount {amount} far exceeds average {avg_amount}',
                        'severity': 'MEDIUM'
                    })
                    break
        
        # Generate alerts for anomalies
        if anomalies and self.monitored_addresses[address]['alert_on_anomaly']:
            for anomaly in anomalies:
                self._generate_alert(
                    address=address,
                    alert_type=anomaly['type'],
                    severity=anomaly['severity'],
                    description=anomaly['description'],
                    metadata=anomaly
                )
            
            self.monitored_addresses[address]['anomalies_detected'] += len(anomalies)
    
    def _check_for_new_counterparties(self, address: str):
        """Detect new counterparties"""
        config = self.monitored_addresses[address]
        
        recent_txs = self.transaction_history.get(address, [])[-10:]
        new_counterparties = []
        
        for tx in recent_txs:
            counterparty = tx.get('to') if tx.get('from') == address else tx.get('from')
            
            if counterparty and counterparty not in config['known_counterparties']:
                new_counterparties.append(counterparty)
                config['known_counterparties'].add(counterparty)
        
        if new_counterparties:
            self._generate_alert(
                address=address,
                alert_type='new_counterparty',
                severity='LOW',
                description=f"New counterparties detected: {len(new_counterparties)}",
                metadata={'new_counterparties': new_counterparties}
            )
    
    def _generate_alert(self, address: str, alert_type: str, 
                       severity: str, description: str, metadata: Dict = None):
        """Generate alert"""
        
        alert = {
            'id': len(self.alerts),
            'address': address,
            'alert_type': alert_type,
            'severity': severity,
            'description': description,
            'metadata': metadata or {},
            'generated_at': datetime.utcnow().isoformat(),
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        
        # Log alert
        severity_icon = '🔴' if severity == 'CRITICAL' else '🟠' if severity == 'HIGH' else '🟡'
        print(f"{severity_icon} [{severity}] {alert_type}: {description}")
    
    def get_alerts(self, address: str = None, severity: str = None, 
                  unacknowledged_only: bool = False) -> List[Dict]:
        """Get alerts (filtered)"""
        
        alerts = self.alerts
        
        if address:
            alerts = [a for a in alerts if a['address'].lower() == address.lower()]
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        if unacknowledged_only:
            alerts = [a for a in alerts if not a['acknowledged']]
        
        return alerts
    
    def acknowledge_alert(self, alert_id: int):
        """Mark alert as acknowledged"""
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id]['acknowledged'] = True
            return True
        return False
    
    def get_monitoring_status(self) -> Dict:
        """Get status of all monitored addresses"""
        
        status = {
            'monitoring_active': len(self.monitored_addresses) > 0,
            'total_monitored': len(self.monitored_addresses),
            'check_interval_seconds': self.check_interval,
            'total_checks_performed': sum(a['check_count'] for a in self.monitored_addresses.values()),
            'total_anomalies': sum(a['anomalies_detected'] for a in self.monitored_addresses.values()),
            'total_alerts': len(self.alerts),
            'addresses': {}
        }
        
        for addr, config in self.monitored_addresses.items():
            status['addresses'][addr] = {
                'chain': config['chain'],
                'added_at': config['added_at'].isoformat(),
                'last_checked': config['last_checked'].isoformat() if config['last_checked'] else None,
                'checks_performed': config['check_count'],
                'anomalies_detected': config['anomalies_detected'],
                'last_tx_count': config['last_tx_count'],
                'status': 'ACTIVE' if config['is_active'] else 'PAUSED'
            }
        
        return status
    
    def export_alerts(self, filepath: str = 'exports/monitoring_alerts.json'):
        """Export alerts to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                'exported_at': datetime.utcnow().isoformat(),
                'total_alerts': len(self.alerts),
                'alerts': self.alerts
            }, f, indent=2)
        
        print(f"✓ Alerts exported to {filepath}")


# Dashboard update callback
def update_dashboard_callback(monitoring: RealTimeMonitor):
    """Callback to update web dashboard with new alerts"""
    status = monitoring.get_monitoring_status()
    
    # This would be called via WebSocket to push updates to clients
    print(f"\n[Dashboard] Updated: {status['total_alerts']} total alerts")
    print(f"[Dashboard] Monitoring {status['total_monitored']} addresses")
    
    # In production: broadcast via WebSocket
    # broadcast_to_clients('monitoring_update', status)


def test_monitoring():
    """Test monitoring system"""
    monitor = RealTimeMonitor()
    
    # Add test address
    monitor.add_address('0xd8da6bf26964af9d7eed9e03e53415d37aa96045', 'ethereum')
    
    # Simulate checking
    print("\nSimulating monitoring checks...\n")
    for i in range(3):
        monitor.check_all_addresses()
        print(f"Iteration {i+1} complete")
        time.sleep(2)
    
    # Get status
    status = monitor.get_monitoring_status()
    print("\n[Status]")
    print(json.dumps(status, indent=2))
    
    # Get alerts
    alerts = monitor.get_alerts(unacknowledged_only=True)
    print(f"\n[Alerts] {len(alerts)} unacknowledged")


if __name__ == '__main__':
    test_monitoring()
