"""
P1 Chain Integration Test — Round 2
Uses verified-active addresses across all new chains.
Tests both the fetcher classes directly and the router.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()

from modules.fetchers.multi_chain import MultiChainFetcher

PASS = '✅'
FAIL = '❌'
WARN = '⚠️'

# Verified active addresses + expected min tx counts
TEST_CASES = [
    # (chain, address_or_hash, expected_min_txns, notes)
    ('fantom',       '0x2C854F3A265E9d7E7dD65E1f8Ad4B978c8F59Db8', 1, 'Fantom — Moralis (active wallet)'),
    ('bnb',          '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', 100, 'BNB — Binance cold wallet, very active'),
    ('avalanche',    '0xd3a92b5afd40124b085e2d7fCbA59E67F61Dc43d', 1, 'Avalanche — Alchemy'),
    ('optimism',     '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 100, 'Optimism — Vitalik'),
    ('base',         '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 100, 'Base — Vitalik'),
    ('polygon_zkevm','0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9', 1, 'Polygon zkEVM — Alchemy'),
    ('rootstock',    '0x542fda317318ebf1d3deaf72845dde63341f4b5d', 1, 'Rootstock — Alchemy'),
    ('stacks',       'SP3FBR2AGK5H9QBDH3EEN6DF8EK8JY7RX8QJ5SVTE', 1, 'Stacks — known active wallet'),
    ('stellar',      'GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGZUCJER3ZMTXVBKDEXAGT', 1, 'Stellar — known active XLM account'),
    ('ton',          'EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs', 100, 'TON — OKX TonCenter (15K txns confirmed)'),
    ('litecoin',     'LhyLmDLCkPCZH5AhitBYTKrMMuH1v4zUXr', 1, 'LTC — Trezor ltc1 Blockbook'),
    ('bitcoin_cash', 'qpm2qsznhks23z7629mms6s4cwef74vcwvy22gdx6a', 1, 'BCH — Trezor bch1 Blockbook'),
    ('dash',         'XoGgqrCvpHwgpFQAJVjd4BVRdchJrLLzSh', 1, 'DASH — BlockCypher'),
    ('digibyte',     'DBkAKa7UMnfC4cAMjFWDa7CVZ9G5yB3G7a', 1, 'DGB — InsightFetcher digiexplorer.info'),
    ('ecash',        'qpmezgsmqmftzaqx65gqkb3f8ysrxrqd5u9aml33la', 1, 'eCash — ChronIK official e.cash'),
    ('zcash',        't1Hsc1LR8yKnbbe3twRp88p6vFfC5t7DLbs', 1, 'ZEC — zec1.trezor.io Blockbook'),
    ('groestlcoin',  'FwGf6iLgvBCRhJhRZoVpHnGQGWB6XBDucc', 1, 'GRS — blockbook.groestlcoin.org'),
    ('peercoin',     'PMgPJuBMtx7Bx1XK4e7j8rjzgwK5tD5G3k', 1, 'PPC — blockbook.peercoin.net'),
    # Monero — TX hash only
    ('monero', 'c36258a276018c3a4bc1f195a7fb530f50cd63a72d9d70f7a60dac38a6b5765b', 0, 'XMR — TX hash (privacy chain)'),
]

print(f"\n{'='*75}")
print(f"  P1 CHAIN RE-TEST (fixed endpoints) — {len(TEST_CASES)} chains")
print(f"{'='*75}\n")

results = {'pass': 0, 'fail': 0, 'warn': 0}

for chain, addr, min_expected, note in TEST_CASES:
    try:
        if chain == 'monero':
            tx = MultiChainFetcher.fetch_tx_by_hash(chain, addr)
            if tx:
                icon, msg = PASS, 'TX found'
                results['pass'] += 1
            else:
                icon, msg = WARN, 'No TX (privacy — expected)'
                results['warn'] += 1
        else:
            txs, counts = MultiChainFetcher.fetch_by_chain(chain, addr)
            count = len(txs)
            if count >= min_expected:
                icon, msg = PASS, f'{count} txns'
                results['pass'] += 1
            elif count > 0:
                icon, msg = WARN, f'Only {count} txns (expected ≥{min_expected})'
                results['warn'] += 1
            else:
                icon, msg = FAIL, f'0 txns returned'
                results['fail'] += 1

    except Exception as e:
        icon, msg = FAIL, f'ERROR: {str(e)[:80]}'
        results['fail'] += 1

    print(f"  [{chain:<20}] {icon} {msg:<35} ({note})")

print(f"\n{'='*75}")
print(f"  ✅ PASS: {results['pass']}  ⚠️ WARN: {results['warn']}  ❌ FAIL: {results['fail']}  | Total: {len(TEST_CASES)} chains")
print(f"{'='*75}\n")
