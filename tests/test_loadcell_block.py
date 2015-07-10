from unittest.mock import patch, MagicMock
from collections import defaultdict
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..load_cell_block import LoadCell

sample_data = (b'B035851000197104100\r'
               b'A035848000000104100\r'
               b'B035851000197104100\r'
               b'A035848000104104100\r'
               b'B035851000197104100\r')

sample_data_0 = (b'B035851000197104100\r')
sample_data_1 = (b'A035848000000104100\r')

class TestLoadCellBlock(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        # This will keep a list of signals notified for each output
        self.last_notified = defaultdict(list)

    def signals_notified(self, signals, output_id='default'):
        self.last_notified[output_id].extend(signals)

    def x___signals_notified(self, signals):
        self._signals = signals

    def test_load_cell_read(self):
        blk = LoadCell()
        self.configure_block(blk, {'address': ''})
        with patch('serial.Serial'):
            blk.start()
        blk._parse(sample_data_0)
        blk._parse(sample_data_1)
        blk.stop()
        self.assert_num_signals_notified(2, blk)
        self.assertEqual(self.last_notified['default'][0].load['weight'], 197)
