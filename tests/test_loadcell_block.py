from nio.modules.threading import sleep
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.scheduler import SchedulerModule
from nio.common.signal.base import Signal

from ..load_cell_block import LoadCell

data = (b'B035851000197104100\rA035848000000104100\rB035851000197104100\r' +
        b'A035848000104104100\rB035851000197104100\r')


class TestLoadCellBlock(NIOBlockTestCase):
    def signals_notified(self, signals):
        self._signals = signals

    def test_load_cell_read(self):
        notified = 0

        blk = LoadCell()
        self.configure_block(blk, {'address': ''})
        blk.start()
        blk._parse(data)
        notified += 5
        self.assert_num_signals_notified(notified, blk)
        self.assertEqual(self._signals[0].load['weight'], 197)
