import os
from etherscan_v2 import EtherscanV2
import unittest

class TestEtherscanV2(unittest.TestCase):
    def setUp(self):
        api_key = os.getenv("ETHERSCAN_API_KEY", "demo")
        self.escan = EtherscanV2(api_key)
        self.address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    def test_eth_balance(self):
        result = self.escan.get_balance(self.address, 1)
        self.assertIsInstance(result, float)

    def test_bnb_balance(self):
        result = self.escan.get_balance(self.address, 56)
        self.assertIsInstance(result, float)

    def test_polygon_balance(self):
        result = self.escan.get_balance(self.address, 137)
        self.assertIsInstance(result, float)

    def test_invalid_chain(self):
        with self.assertRaises(ValueError):
            self.escan.get_balance_by_name(self.address, "invalidchain")

if __name__ == "__main__":
    unittest.main()
    except Exception as je:
        print(f"JSON Parse ERROR: {je}")
except Exception as e:
    print(f"Request ERROR: {e}")

print("\n" + "="*60)
