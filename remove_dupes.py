import os
import re

# List from user of exactly what overlaps between Etherscan and Alchemy:
# Sepolia, Worldchain, Berachain, Monad, Plasma, Stable, Sonic, Unichain, Apechain, MegaETH, Abstract

# Inside our multi_chain.py, Etherscan mapping holds:
# 'sepolia', 'world', 'world_sepolia', 'berachain', 'berachain_testnet', 'monad', 'monad_testnet',
# 'plasma', 'plasma_testnet', 'stable', 'stable_testnet', 'sonic', 'sonic_testnet', 
# 'unichain', 'unichain_sepolia', 'apechain', 'apechain_curtis', 'megaeth', 'megaeth_testnet',
# 'abstract', 'abstract_testnet'

def remove_duplicates_from_etherscan():
    multi_chain_file = os.path.join('modules', 'fetchers', 'multi_chain.py')
    with open(multi_chain_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # We will identify the keys to remove from EtherscanMultiChainFetcher.CHAIN_CONFIGS
    keys_to_remove = [
        "'sepolia'", "'world'", "'world_sepolia'", "'berachain'", "'berachain_testnet'",
        "'monad'", "'monad_testnet'", "'plasma'", "'plasma_testnet'", "'stable'", "'stable_testnet'",
        "'sonic'", "'sonic_testnet'", "'unichain'", "'unichain_sepolia'", "'apechain'",
        "'apechain_curtis'", "'megaeth'", "'megaeth_testnet'", "'abstract'", "'abstract_testnet'"
    ]
    
    # We will regex out the dictionary items matching these keys inside CHAIN_CONFIGS
    for key in keys_to_remove:
        # Match pattern like: 'world': { ... },
        pattern = r"\s+" + key + r":\s*\{[^}]+\},"
        content = re.sub(pattern, "", content)
        
        # also match without trailing comma if it's the last item
        pattern_last = r"\s+" + key + r":\s*\{[^}]+\}"
        content = re.sub(pattern_last, "", content)

    with open(multi_chain_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Removed {len(keys_to_remove)} duplicate overlapping keys from multi_chain.py")

if __name__ == '__main__':
    remove_duplicates_from_etherscan()
