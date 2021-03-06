from threading import Event
from unittest.mock import patch

from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from nio.util.discovery import not_discoverable

from ..load_cell_block import LoadCell

sample_data = (b'B035851000197104100\r'
               b'A035848000000104100\r'
               b'B035851000197104100\r'
               b'A035848000104104100\r'
               b'B035851000197104100\r')
sample_data_0 = (b'B035851000197104100\r')
sample_data_1 = (b'A035848000000104100\r')


@not_discoverable
class LoadCellParseEvent(LoadCell):

    def __init__(self, event):
        super().__init__()
        self._parse_limit = 1
        self._parse_count = 0
        self._event = event

    def _parse_and_notify(self, sdata):
        super()._parse_and_notify(sdata)
        self._parse_count += 1
        self.logger.debug(
            'Incrementing parse count to {}'.format(self._parse_count))
        if self._parse_count >= self._parse_limit:
            self.logger.debug('Set parse event')
            self._event.set()


class TestLoadCellBlock(NIOBlockTestCase):

    def test_load_cell_readline(self):
        e = Event()
        blk = LoadCellParseEvent(e)
        self.configure_block(blk, {'address': ''})
        with patch('serial.Serial'):
            blk.start()
        blk._com.read.side_effect = \
            [b'B', b'0', b'3', b'\r',
             b'B', b'0', b'3', b'5', b'8', b'5', b'1', b'0', b'0', b'0',
             b'1', b'9', b'7', b'1', b'0', b'4', b'1', b'0', b'0', b'\r']
        # wait for first parse
        e.wait(1.5)
        blk.stop()
        self.assert_num_signals_notified(1, blk)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {
                'load': {
                    'battery': 100,
                    'id': 35851,
                    'temperature': 104,
                    'token': 'B',
                    'weight': 197
                }
            }
        )

    def test_load_cell_read_exception(self):
        """Log a WARNING when a serial read raises an exception"""
        e = Event()
        blk = LoadCellParseEvent(e)
        self.configure_block(blk, {'address': ''})
        with patch('serial.Serial'):
            blk.start()
        blk._com.read.side_effect = [
            # Incomplete line to start
            b'B', b'0', b'3', b'\r', \
            # Then one that fails
            b'B', b'0', b'3', b'5', b'8', b'5', b'1', b'0', b'0', b'0', \
            Exception,
            # Then a good read
            b'B', b'0', b'3', b'5', b'8', b'5', b'1', b'0', b'0', b'0', \
            b'1', b'9', b'7', b'1', b'0', b'4', b'1', b'0', b'0', b'\r']
        # wait for first parse
        e.wait(1.5)
        blk.stop()
        self.assert_num_signals_notified(1, blk)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {
                'load': {
                    'battery': 100,
                    'id': 35851,
                    'temperature': 104,
                    'token': 'B',
                    'weight': 197
                }
            }
        )

    def test_load_cell_parse(self):
        blk = LoadCell()
        self.configure_block(blk, {'address': ''})
        with patch('serial.Serial'):
            blk.start()
        blk._parse_and_notify(sample_data_0)
        blk._parse_and_notify(sample_data_1)
        blk.stop()
        self.assert_num_signals_notified(2, blk)
        self.assertEqual(
            self.last_notified[DEFAULT_TERMINAL][0].load['weight'], 197)
