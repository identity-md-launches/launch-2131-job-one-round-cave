import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name('balance_slot.py')
spec = importlib.util.spec_from_file_location('balance_slot_tested', MODULE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class BalanceSlotTests(unittest.TestCase):
    def test_real_address_derivation(self):
        result = tool.derive(tool.ZTO, tool.POOL_MANAGER, 0)
        self.assertEqual(result['preimage'],
                         '0x' + '00' * 12 + tool.POOL_MANAGER[2:] + '00' * 32)
        self.assertEqual(result['storageSlot'],
                         '0x11fd237061433ba9f221f703bed587e7636b11fbe3815abba27443968931d654')
        self.assertIn('independently confirm', result['assumption'])

    def test_slot_bounds_and_addresses(self):
        with self.assertRaises(tool.w.Invalid):
            tool.derive(tool.ZTO, tool.POOL_MANAGER, 1 << 256)
        with self.assertRaises(tool.w.Invalid):
            tool.derive(tool.ZTO, '0x12', 0)

    def test_mapping_slot_cli_parsing(self):
        self.assertEqual(tool.parse_mapping_slot('17'), 17)
        self.assertEqual(tool.parse_mapping_slot('0x11'), 17)
        with self.assertRaises(Exception):
            tool.parse_mapping_slot('-1')


if __name__ == '__main__':
    unittest.main()
