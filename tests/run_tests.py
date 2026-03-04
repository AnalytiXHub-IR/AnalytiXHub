import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv()
from modules.fetchers.multi_chain import MultiChainFetcher

# Vitalik addresses used for active chains where possible
TEST_CASES = [
    ('fantom',       '0xcb9bdfbeeb0f5854bace9ecaa89f921588d92661', 'FTM'),
    ('bnb',          '0x8894E0a0c962CB723c1976a4421c95949bE2D4E3', 'BSC'),
    ('avalanche',    '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'AVAX (Vitalik)'),
    ('optimism',     '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'OP (Vitalik)'),
    ('base',         '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'Base (Vitalik)'),
    ('polygon_zkevm','0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'ZkEVM (Vitalik)'),
    ('rootstock',    '0x0000000000000000000000000000000001000006', 'Rootstock'),
    ('stacks',       'SP3FBR2AGK5H9QBDH3EEN6DF8EK8JY7RX8QJ5SVTE', 'Stacks'),
    ('stellar',      'GCOHEGB2M2UXXBFWV6E7CUC2NY2XQ66U42E4P6Y3E2KVHPEOFRW6I3X2', 'Stellar'),
    ('ton',          'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs', 'TON'),
    ('litecoin',     'LUSfWvtyCZbBw9bT9ZMY2FjQ4G7T3N45gZ', 'LTC'),
    ('bitcoin_cash', 'bitcoincash:qpz0zqqxxvqrqpzyqqzpqqzqpqqzqqz0qyyqszqszq', 'BCH'),
    ('dash',         'XoGgqrCvpHwgpFQAJVjd4BVRdchJrLLzSh', 'DASH'),
    ('digibyte',     'D51xsYf3K2BWhZ9iFjGvto4C1oDBrT8Z5T', 'DGB'),
    ('ecash',        'ecash:qpz0zqqxxvqrqpzyqqzpqqzqpqqzqqz0qyqqw8j8kq', 'eCash'),
    ('zcash',        't1XyYfF3f9G3hZ8b3LZbRbR4T5tJtU5e1mX', 'ZEC'),
    ('groestlcoin',  'FwGf6iLgvBCRhJhRZoVpHnGQGWB6XBDucc', 'GRS'),
    ('peercoin',     'PMgPJuBMtx7Bx1XK4e7j8rjzgwK5tD5G3k', 'PPC'),
]

print('\n=== FINAL COMPLETE VALIDATION RUN ===\n')
for chain, addr, note in TEST_CASES:
    try:
        tx, _ = MultiChainFetcher.fetch_by_chain(chain, addr)
        count = len(tx) if isinstance(tx, list) else (1 if tx else 0)
        status = '✅ PASS' if count > 0 else '❌ FAIL'
        print(f'[{chain.upper()}] {status}: {count} txns ({note})')
    except Exception as e:
        print(f'[{chain.upper()}] ❌ ERROR: {e} ({note})')
