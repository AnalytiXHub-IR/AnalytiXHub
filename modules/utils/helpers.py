from web3 import Web3

def normalize_address(address, chain_id_or_name):
    """
    Normalize address based on chain type.
    EVM -> Checksum Capitalization (EIP-55)
    Non-EVM (Solana, Bitcoin, Tron) -> Case Sensitive Raw
    """
    c = str(chain_id_or_name).lower()
    
    # Assume EVM by default unless explicitly in out non-EVM list
    is_evm = True
    non_evm_names = ['sol', 'solana', 'btc', 'bitcoin', 'tron', 'trx', 'xrp', 'ripple', 'aptos', 'aptos_testnet', 'doge']
    
    if c in non_evm_names:
        is_evm = False
        
    if is_evm and address and isinstance(address, str) and address.startswith('0x'):
        try:
            # We force it to lower() first so Web3 accurately reconstructs the deterministic checksum 
            return Web3.to_checksum_address(address.lower())
        except:
            return address
            
    return address
