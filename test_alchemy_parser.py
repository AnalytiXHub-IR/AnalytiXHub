import sys
import os
import json
from datetime import datetime

# Exact JSON user provided
user_json = """
{"jsonrpc":"2.0","id":1,"result":{"transfers":[{"blockNum":"0xcbe223","uniqueId":"0x70eccdb6aa9f64d49fa9d375e5675001c27941ef3be724434771eb121ad6626d:log:3","hash":"0x70eccdb6aa9f64d49fa9d375e5675001c27941ef3be724434771eb121ad6626d","from":"0xdd186d9e0c6a0ec8731e183a853efb1eec8438ec","to":"0x735b14bb79463307aacbed86daf3322b1e6226ab","value":1.63934946E-7,"erc721TokenId":null,"erc1155Metadata":[],"tokenId":null,"asset":"ETH.BASE","category":"erc20","rawContract":{"value":"0x262b48c2d0","address":""}}]}}
"""

def test_parser():
    data = json.loads(user_json)
    result = data.get('result') or {}
    transfers = result.get('transfers', [])
    all_txs = []
    
    print(f"Loaded {len(transfers)} transfers.")
    
    for tx in transfers:
        try:
            meta = tx.get('metadata') or {}
            timestamp_str = meta.get('blockTimestamp')
            formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if timestamp_str:
                try:
                    if timestamp_str.endswith('Z'):
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
                    else:
                        dt = datetime.fromisoformat(timestamp_str.split('.')[0])
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as ex:
                    print("Date Parse Error:", ex)
                    pass
                    
            block_num_hex = tx.get('blockNum') or '0x0'
            parsed = {
                'hash': tx.get('hash'),
                'from': tx.get('from', 'Unknown') or 'Unknown',
                'to': tx.get('to', 'Unknown') or 'Unknown',
                'value': tx.get('value') or 0.0,
                'timestamp': formatted_time,
                'block': int(block_num_hex, 16),
                'chain': "test_chain",
                'type': tx.get('category', 'transfer')
            }
            all_txs.append(parsed)
            print("Successfully parsed TX!")
        except Exception as e:
            print(f"FAILED ON Parsing TX: {e}")

    print("Parsed output:", all_txs)

if __name__ == "__main__":
    test_parser()
