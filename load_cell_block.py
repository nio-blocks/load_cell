import re
import time
from collections import deque
from threading import Lock
from threading import Thread
from serial import Serial

from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.common.discovery import Discoverable, DiscoverableType


@Discoverable(DiscoverableType.block)
class LoadCell(Block):
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
        self._lock = Lock()
        self.data = deque()
        self._com = None
        self._timeout = 1
        self._eol = b'\n'
        self._kill = False
        self._unparsed = b''
        self.raw = deque()

    def start(self):
        super().start()
        self.fmat = re.compile(self.format.encode()).search
        self._com = Serial(self.address, self.baud)
        self._timeout = 0.05
        self._eol = b'\r' 
        self._com.timeout = self._timeout
        # Read some large amount of bytes to clear the buffer
        self._logger.debug('flush')
        self._com.read(100)
        self._logger.debug('done with flush')
        # read from com port in new thread
        self._thread = Thread(target=self._read_thread)
        self._thread.daemon = True
        self._thread.start()

    def _read_thread(self):
        sleep_time = 0.002
        # discard first line. it may be incomplete.
        time.sleep(1)
        self._readline()
        while not self._kill:
            self._logger.debug('read_thread loop')
            start = time.time()
            self._logger.debug('start time'.format(start))
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
        while latest_byte != self._eol:
            latest_byte = self._com.read(1)
            return_value += latest_byte
        return return_value

    def _parse(self, sdata):
        self._logger.debug('starting block parse')
        self._parse_reader(sdata)
        data = self.data
        name = self.sname
        signals = []
        while data:
            self._logger.debug('prepare signal')
            try:
                signals.append(Signal({name: data.pop()}))
            except:
                self._logger.exception('error preparing signal')
        self._logger.debug('notifying signal')
        if signals:
            self.notify_signals(signals)
        self._logger.debug('done with block parse')

    def _parse_reader(self, sdata):
        self._logger.debug('starting reader parse')
        df = self.fmat
        raw = self.raw
        mydata = self.data
        self._parse_serial(sdata)
        self._logger.debug('raw: {}'.format(raw))
        with self._lock:
            self._logger.debug('has lock')
            while raw:
                self._logger.debug('has raw')
                raw_val = self.raw.pop()
                match = df(raw_val)
                if not match:
                    msg = "Value didn't match: {}".format(raw_val)
                    if self._logger is not None:
                        self._logger.warning(msg)
                    continue
                data = match.groupdict()
                for key, value in data.items():
                    try:
                        # if it can be converted to an integer, do so
                        data[key] = int(value)
                    except (ValueError, TypeError):
                        # otherwise, everything should be a string
                        data[key] = value.decode()

                mydata.appendleft(data)
                self._logger.debug("LC in: {} | out: {}".format(raw_val, data))
            self._logger.debug('done with lock')
        self._logger.debug('done with reader parse')

    def _parse_serial(self, data):
        self._logger.debug('starting serial parse')
        data = data.split(self._eol)
        if len(data) == 1:
            self._unparsed = data[0]
            self._logger.debug('done with serial parse')
            return
        data[0] = b''.join((self._unparsed, data[0]))
        self._unparsed = data.pop()
        self.raw.extendleft(data)
        self._logger.debug('done with serial parse')
