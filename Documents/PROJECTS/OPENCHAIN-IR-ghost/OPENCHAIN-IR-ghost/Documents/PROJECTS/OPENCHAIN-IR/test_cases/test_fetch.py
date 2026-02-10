import os, json, traceback
from dotenv import load_dotenv
load_dotenv()
from eth_live import fetch_eth_address

addr='0x974CaA59e49682CdA0AD2bbe82983419A2ECC400'
key=os.getenv('ETHERSCAN_API_KEY')
print('ETHERSCAN_API_KEY present:', bool(key))
print('Using address:', addr)
try:
    txs = fetch_eth_address(addr, key, include_internal=True, include_token_transfers=True)
    print('Total txs returned:', len(txs))
    if len(txs)>0:
        print('\nSample tx[0]:')
        print(json.dumps(txs[0], indent=2)[:1500])
except Exception as e:
    print('ERROR:', e)
    traceback.print_exc()
