import os

ETHER_CHAINS = {
    'ethereum': {'chainid': 1, 'name': 'Ethereum Mainnet'},
    'sepolia': {'chainid': 11155111, 'name': 'Sepolia Testnet'},
    'hoodi': {'chainid': 560048, 'name': 'Hoodi Testnet'},
    'polygon': {'chainid': 137, 'name': 'Polygon Mainnet'},
    'amoy': {'chainid': 80002, 'name': 'Polygon Amoy Testnet'},
    'arbitrum': {'chainid': 42161, 'name': 'Arbitrum One Mainnet'},
    'arbitrum_sepolia': {'chainid': 421614, 'name': 'Arbitrum Sepolia Testnet'},
    'linea': {'chainid': 59144, 'name': 'Linea Mainnet'},
    'linea_sepolia': {'chainid': 59141, 'name': 'Linea Sepolia Testnet'},
    'blast': {'chainid': 81457, 'name': 'Blast Mainnet'},
    'blast_sepolia': {'chainid': 168587773, 'name': 'Blast Sepolia Testnet'},
    'bttc': {'chainid': 199, 'name': 'BitTorrent Chain Mainnet'},
    'bttc_testnet': {'chainid': 1029, 'name': 'BitTorrent Chain Testnet'},
    'celo': {'chainid': 42220, 'name': 'Celo Mainnet'},
    'celo_sepolia': {'chainid': 11142220, 'name': 'Celo Sepolia Testnet'},
    'fraxtal': {'chainid': 252, 'name': 'Fraxtal Mainnet'},
    'fraxtal_hoodi': {'chainid': 2523, 'name': 'Fraxtal Hoodi Testnet'},
    'gnosis': {'chainid': 100, 'name': 'Gnosis'},
    'mantle': {'chainid': 5000, 'name': 'Mantle Mainnet'},
    'mantle_sepolia': {'chainid': 5003, 'name': 'Mantle Sepolia Testnet'},
    'memecore': {'chainid': 4352, 'name': 'Memecore Mainnet'},
    'memecore_testnet': {'chainid': 43521, 'name': 'Memecore Testnet'},
    'moonbeam': {'chainid': 1284, 'name': 'Moonbeam Mainnet'},
    'moonriver': {'chainid': 1285, 'name': 'Moonriver Mainnet'},
    'moonbase': {'chainid': 1287, 'name': 'Moonbase Alpha Testnet'},
    'opbnb': {'chainid': 204, 'name': 'opBNB Mainnet'},
    'opbnb_testnet': {'chainid': 5611, 'name': 'opBNB Testnet'},
    'scroll': {'chainid': 534352, 'name': 'Scroll Mainnet'},
    'scroll_sepolia': {'chainid': 534351, 'name': 'Scroll Sepolia Testnet'},
    'taiko': {'chainid': 167000, 'name': 'Taiko Mainnet'},
    'taiko_hoodi': {'chainid': 167013, 'name': 'Taiko Hoodi'},
    'xdc': {'chainid': 50, 'name': 'XDC Mainnet'},
    'xdc_testnet': {'chainid': 51, 'name': 'XDC Apothem Testnet'},
    'apechain': {'chainid': 33139, 'name': 'ApeChain Mainnet'},
    'apechain_curtis': {'chainid': 33111, 'name': 'ApeChain Curtis Testnet'},
    'worldchain': {'chainid': 480, 'name': 'World Mainnet'},
    'worldchain_sepolia': {'chainid': 4801, 'name': 'World Sepolia Testnet'},
    'sonic': {'chainid': 146, 'name': 'Sonic Mainnet'},
    'sonic_testnet': {'chainid': 14601, 'name': 'Sonic Testnet'},
    'unichain': {'chainid': 130, 'name': 'Unichain Mainnet'},
    'unichain_sepolia': {'chainid': 1301, 'name': 'Unichain Sepolia Testnet'},
    'abstract': {'chainid': 2741, 'name': 'Abstract Mainnet'},
    'abstract_sepolia': {'chainid': 11124, 'name': 'Abstract Sepolia Testnet'},
    'berachain': {'chainid': 80094, 'name': 'Berachain Mainnet'},
    'berachain_bepolia': {'chainid': 80069, 'name': 'Berachain Bepolia Testnet'},
    'swellchain': {'chainid': 1923, 'name': 'Swellchain Mainnet'},
    'swellchain_testnet': {'chainid': 1924, 'name': 'Swellchain Testnet'},
    'monad': {'chainid': 143, 'name': 'Monad Mainnet'},
    'monad_testnet': {'chainid': 10143, 'name': 'Monad Testnet'},
    'hyperevm': {'chainid': 999, 'name': 'HyperEVM Mainnet'},
    'katana': {'chainid': 747474, 'name': 'Katana Mainnet'},
    'katana_bokuto': {'chainid': 737373, 'name': 'Katana Bokuto'},
    'sei': {'chainid': 1329, 'name': 'Sei Mainnet'},
    'sei_testnet': {'chainid': 1328, 'name': 'Sei Testnet'},
    'stable': {'chainid': 988, 'name': 'Stable Mainnet'},
    'stable_testnet': {'chainid': 2201, 'name': 'Stable Testnet'},
    'plasma': {'chainid': 9745, 'name': 'Plasma Mainnet'},
    'plasma_testnet': {'chainid': 9746, 'name': 'Plasma Testnet'},
    'megaeth': {'chainid': 4326, 'name': 'MegaETH Mainnet'},
    'megaeth_testnet': {'chainid': 6342, 'name': 'MegaETH Testnet'},
}

def patch():
    path = os.path.join('modules', 'fetchers', 'multi_chain.py')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find CHAIN_CONFIGS = { ... }
    start = content.find('CHAIN_CONFIGS = {')
    if start == -1:
        print("Could not find CHAIN_CONFIGS")
        return
    
    end = content.find('    }', start)
    if end == -1:
        print("Could not find end of CHAIN_CONFIGS")
        return

    # Build new string
    new_str = "CHAIN_CONFIGS = {\n"
    for k, v in ETHER_CHAINS.items():
        new_str += f"        '{k}': {{'chainid': {v['chainid']}, 'name': '{v['name']}'}},\n"
    new_str += "    }"

    new_content = content[:start] + new_str + content[end + 5:]
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Patched CHAIN_CONFIGS")

if __name__ == '__main__':
    patch()
