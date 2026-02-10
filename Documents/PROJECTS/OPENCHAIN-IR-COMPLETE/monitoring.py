from datetime import datetime
import json
import os

class MonitoringSystem:
    """
    Manages a watchlist of addresses and performs periodic checks for new activity.
    """
    def __init__(self, data_file='monitoring_data.json'):
        self.data_file = data_file
        self.watchlist = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.watchlist, f, indent=4)

    def add_address(self, address, chain='ethereum', tag='watchlist'):
        address = address.lower()
        if address not in self.watchlist:
            self.watchlist[address] = {
                'address': address,
                'chain': chain,
                'tag': tag,
                'added_at': datetime.now().isoformat(),
                'last_check': None,
                'status': 'active',
                'alerts': []
            }
            self._save_data()
            return True
        return False

    def remove_address(self, address):
        address = address.lower()
        if address in self.watchlist:
            del self.watchlist[address]
            self._save_data()
            return True
        return False

    def get_watchlist(self):
        return list(self.watchlist.values())

    def get_alerts(self):
        # Flatten alerts from all addresses
        all_alerts = []
        for addr, data in self.watchlist.items():
            for alert in data.get('alerts', []):
                alert['address'] = addr
                all_alerts.append(alert)
        return sorted(all_alerts, key=lambda x: x['timestamp'], reverse=True)
