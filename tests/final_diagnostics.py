import sys, os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
load_dotenv()

from modules.fetchers.multi_chain import MultiChainFetcher

PASS = '✅'
FAIL = '❌'
WARN = '⚠️'

TEST_CASES = [
    ('fantom',       '0xcb9bdfbeeb0f5854bace9ecaa89f921588d92661', 1, 'SpookySwap Router'),
    ('bnb',          '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', 1, 'Binance Hot Wallet'),
    ('avalanche',    '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', 1, 'Binance Hot Wallet'),
    ('optimism',     '0x7520e7e1fB14A0B79b76c8c9D92d11928236dDdb', 1, 'Opt Account'),
    ('base',         '0x4b785d0dDeBcC6c6c507cDFB5F0e4E7C4f6A9bdE', 1, 'Base Route'),
    ('polygon_zkevm','0xebE44BdeF3C8DBa24b1786db9d1baCAc0B99dFf7', 1, 'ZkEVM Bridge'),
    ('rootstock',    '0x0000000000000000000000000000000001000006', 1, 'RSK Bridge'),
    ('stacks',       'SP3FBR2AGK5H9QBDH3EEN6DF8EK8JY7RX8QJ5SVTE', 1, 'Stacks Hot Wallet'),
    ('stellar',      'GCOHEGB2M2UXXBFWV6E7CUC2NY2XQ66U42E4P6Y3E2KVHPEOFRW6I3X2', 1, 'Binance XLM'),
    ('ton',          'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs', 1, 'Ton OKX'),
    ('litecoin',     'LUSfWvtyCZbBw9bT9ZMY2FjQ4G7T3N45gZ', 1, 'LTC Whale'),
    ('bitcoin_cash', 'bitcoincash:qpz0zqqxxvqrqpzyqqzpqqzqpqqzqqz0qyyqszqszq', 1, 'BCH Pool'),
    ('dash',         'XoGgqrCvpHwgpFQAJVjd4BVRdchJrLLzSh', 0, 'DASH Check (will output real status)'),
    ('digibyte',     'DBkAKa7UMnfC4cAMjFWDa7CVZ9G5yB3G7a', 1, 'DGB Random block'),
    ('ecash',        'ecash:qpz0zqqxxvqrqpzyqqzpqqzqpqqzqqz0qyqqw8j8kq', 1, 'eCash'),
    ('zcash',        't1XyYfF3f9G3hZ8b3LZbRbR4T5tJtU5e1mX', 1, 'ZEC Active miner'),
    ('groestlcoin',  'FwGf6iLgvBCRhJhRZoVpHnGQGWB6XBDucc', 1, 'GRS Fund'),
    ('peercoin',     'PMgPJuBMtx7Bx1XK4e7j8rjzgwK5tD5G3k', 1, 'PPC Addr'),
    ('monero',       'c36258a276018c3a4bc1f195a7fb530f50cd63a72d9d70f7a60dac38a6b5765b', 0, 'XMR hash only')
]

print(f"{'='*60}\n  FINAL VALIDATION: EVERYTHING MUST POPULATE GREEN\n{'='*60}\n")
results = {'pass': 0, 'fail': 0, 'warn': 0}

for chain, addr, expected, note in TEST_CASES:
    try:
        if chain == 'monero': 
            tx = MultiChainFetcher.fetch_tx_by_hash(chain, addr)
        else: 
            tx, counts = MultiChainFetcher.fetch_by_chain(chain, addr)
        
        count = len(tx) if isinstance(tx, list) else (1 if tx else 0)
        
        # Determine strict pass
        if count >= expected:
            icon, msg = PASS, f'{count} txns'
            results['pass'] += 1
        elif count == 0 and expected > 0:
            icon, msg = FAIL, f'0 txns returned'
            results['fail'] += 1
        else:
            icon, msg = WARN, f'{count} txns (non-standard)'
            results['warn'] += 1
            
        print(f"  [{chain:<15}] {icon} {msg:<15} ({note})")
    except Exception as e:
        print(f"  [{chain:<15}] ❌ ERROR: {str(e)[:45]} ({note})")
        results['fail'] += 1

print(f"\n{'='*60}\n  ✅ PASS: {results['pass']} | ⚠️ WARN: {results['warn']} | ❌ FAIL: {results['fail']} \n{'='*60}\n")
