from web3 import Web3

def normalize_address(address, chain_id_or_name):
    """
    Normalize address based on chain type.
    EVM -> Lowercase
    Non-EVM (Solana, Bitcoin, Tron) -> Case Sensitive
    """
    # Determine chain type
    # EVM Chains (by ID or Name)
    evm_ids = [1, 56, 137, 10, 42161, 43114, 250, 25]
    evm_names = ['eth', 'ethereum', 'bsc', 'binance', 'matic', 'polygon', 'optimism', 'op', 'arbitrum', 'arb', 'avalanche', 'fantom', 'base', 'linea', 'blast', 'sepolia']
    
    c = str(chain_id_or_name).lower()
    
    # Check if EVM
    is_evm = False
    if c.isdigit():
        if int(c) in evm_ids or int(c) > 0: # Default assumption: Positive ID is EVM usually
           is_evm = True
           # Special negative IDs for non-EVM
           if int(c) <= 0: is_evm = False 
    else:
        if c in evm_names:
            is_evm = True
    
    # Override for specific Non-EVM names
    if c in ['sol', 'solana', 'btc', 'bitcoin', 'tron', 'trx', 'xrp', 'ripple']:
        is_evm = False
        
    if is_evm and address and isinstance(address, str) and address.startswith('0x'):
        try:
            return Web3.to_checksum_address(address)
        except:
            return address
            
    return address
