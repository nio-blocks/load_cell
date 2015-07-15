import re
import time
import serial
from collections import deque
from nio.modules.threading import Thread
from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.version import VersionProperty
from nio.common.discovery import Discoverable, DiscoverableType


@Discoverable(DiscoverableType.block)
class LoadCell(Block):

    version = VersionProperty('0.1.0')
    sname = StringProperty(title="Signal Name", default="load")
    format = StringProperty(title="Format",
                            default=r'(?P<token>[a-zA-Z])(?P<id>\w*)'
                            r'(?P<weight>\d{6})(?P<temperature>\d{3})'
                            r'(?P<battery>\d{3})')
    address = StringProperty(title="Address", default='/dev/ttyUSB0')
    baud = IntProperty(title="Baud", default=115200)

    def __init__(self):
        super().__init__()
        self.fmat = None
        self._com = None
        self._timeout = 0.05
        self._eol = b'\r'
        self._kill = False

    def start(self):
        super().start()
        self.fmat = re.compile(self.format.encode()).search
        self._com = serial.Serial(self.address, self.baud)
        # Read some large amount of bytes to clear the buffer
        self._logger.debug('flush')
        self._com.timeout = 0.15
        self._com.read(100) # TODO: properly flush buffer at start
        self._com.timeout = self._timeout
        self._logger.debug('done with flush')
        # Read from com port in new thread
        self._thread = Thread(target=self._read_thread)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._kill = True
        super().stop()

    def _read_thread(self):
        sleep_time = 0.002
        # Discard first line. it may be incomplete.
        time.sleep(1)
        self._readline()
        # Read until block stops
        while not self._kill:
            self._logger.debug('read_thread loop')
            start = time.time()
            self._logger.debug('start time: {}'.format(start))
            self._parse(self._readline())
            self._logger.debug('done with parse')
            try:
                self._logger.debug('try sleep')
                time.sleep(sleep_time - (time.time() - start))
                self._logger.debug('wake up!')
            except ValueError:
                self._logger.debug('sleep error')
                pass

    def _readline(self):
        self._logger.debug('readline')
        return_value = b''
        latest_byte = b''
        while latest_byte != self._eol and not self._kill:
            # TODO: This would be much faster if it read more than one byte
            latest_byte = self._com.read(1)
            return_value += latest_byte
        self._logger.debug('line read: {}'.format(return_value))
        return return_value

    def _parse(self, sdata):
        self._logger.debug('starting block parse')
        data = self._parse_raw_into_dict(sdata)
        signals = []
        if data:
            self._logger.debug('prepare signal')
            try:
                signals.append(Signal({self.sname: data}))
            except:
                self._logger.exception('error preparing signal')
        self._logger.debug('notifying signal')
        if signals:
            self.notify_signals(signals)
        self._logger.debug('done with block parse')

    def _parse_raw_into_dict(self, sdata):
        self._logger.debug('starting reader parse')
        raw = sdata
        self._logger.debug('raw: {}'.format(raw))
        data = None
        if raw:
            match = self.fmat(raw)
            if not match:
                msg = "Value didn't match: {}".format(raw)
                self._logger.warning(msg)
                return data
            data = match.groupdict()
            for key, value in data.items():
                try:
                    # if it can be converted to an integer, do so
                    data[key] = int(value)
                except (ValueError, TypeError):
                    # otherwise, everything should be a string
                    data[key] = value.decode()
            self._logger.debug("LC in: {} | out: {}".format(raw, data))
        self._logger.debug('done with reader parse')
        return data
