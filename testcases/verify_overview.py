import sys
import os

# Ensure modules package is accessible from test directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.fetchers.multi_chain import MultiChainFetcher

# Common heavy wallets for robust testing
test_wallets = {
    'evm': '0x9d2bCc598a30cC54AF0D9B021Fb24Be41A46F171', # Lightweight test wallet
    'solana': '5Q544fKrFoe6tsEbD7S8EmxPoCYAWcZc4wN8X59iW2eD',
    'bitcoin': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
    'tron': 'TE2RzoSV3wFK99w6J9UnnZ4vLfXYoxvRwP',
    'aptos': '0x889add27cfbd2432ae9f6d6c1df807e3350ddad7de6f3ec8bdf5fbf920cc70d0', 
    'dogecoin': 'DSaN7XWaEa1nF8k16JzMvVjFhR8D8zE6F3',
    'xrp': 'rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh'
}

chains_to_test = [
    # BlockScout Fallbacks (Previously restricted by Etherscan & Alchemy)
    ('base', 'evm'),
    ('gnosis', 'evm'),
    ('celo', 'evm'),
    ('blast', 'evm'),
    ('linea', 'evm'),
    ('polygon_zkevm', 'evm'),
    ('mantle', 'evm'),
    ('bob', 'evm'),
    ('botanix', 'evm'),
    ('galactica', 'evm'),
    ('opbnb', 'evm'),
    ('sei', 'evm'),
    
    # Alchemy EVM L2s
    ('zksync', 'evm'),
    ('scroll', 'evm'),
    ('beacon', 'evm'),
    ('rootstock', 'evm'),
    
    # Alchemy Non-EVMs
    ('aptos', 'aptos'),
]

def run_verification():
    print("========================================")
    print("Multi-Chain Endpoint Integrity Test")
    print("========================================")
    
    for chain, typ in chains_to_test:
        address = test_wallets[typ]
        print(f"\n[TESTING] {chain.upper():<15} (Wallet: {address[:12]}...)")
        try:
            # We bypass DB and immediately external fetch for verification
            txs, counts = MultiChainFetcher.fetch_by_chain(chain, address, include_internal=False, include_token_transfers=False)
            total = len(txs)
            
            if total > 0:
                print(f"  [SUCCESS]: {total} transactions grabbed")
                print(f"  [SAMPLE]:  {txs[0].get('hash')}")
            else:
                print(f"  [WARN]: 0 transactions (Endpoint returned nothing)")
        except Exception as e:
            import traceback
            print(f"  [FAIL]: Crashed -> {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    run_verification()
