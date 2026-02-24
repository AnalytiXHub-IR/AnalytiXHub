from app import EtherscanMultiChainFetcher, SolanaFetcher
import os
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
SOLANA_API_KEY = os.getenv("SOLANA_API_KEY")  # Helius API Key

def debug_fetch(chain, address):
    print(f"--- Debugging {chain} fetch for {address} ---")
    
    transactions = []
    if chain == 'solana':
        fetcher = SolanaFetcher(SOLANA_API_KEY)
        transactions = fetcher.fetch_transactions(address)
    else:
        # Default to EVM
        fetcher = EtherscanMultiChainFetcher(ETHERSCAN_KEY)
        transactions = fetcher.fetch_transactions(address, chain=chain)
        
    print(f"Fetched {len(transactions)} transactions")
    if len(transactions) > 0:
        print(f"First transaction sample: {transactions[0]}")
        print(f"Keys in first transaction: {transactions[0].keys()}")
        
    return transactions

if __name__ == "__main__":
    # Test with the address user was likely using or a known one
    # Assuming Ethereum/EVM based on context (428 txs is a lot for testnet)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Vitalik's address as sample
    debug_fetch("ethereum", test_address)
