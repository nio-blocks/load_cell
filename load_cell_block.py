import re
import serial
from threading import Thread
import time
from nio.block.base import Block
from nio.signal.base import Signal
from nio.properties import StringProperty, IntProperty, VersionProperty
from nio.util.discovery import discoverable


@discoverable
class LoadCell(Block):

    version = VersionProperty('0.1.0')
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
        self.fmat = re.compile(self.format().encode()).search
        self._com = serial.Serial(self.address(), self.baud())
        # Read some large amount of bytes to clear the buffer
        self.logger.debug('flush')
        self._com.timeout = 0.15
        self._com.read(100) # TODO: properly flush buffer at start
        self._com.timeout = self._timeout
        self.logger.debug('done with flush')
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
            self.logger.debug('read_thread loop')
            start = time.time()
            self.logger.debug('start time: {}'.format(start))
            line = self._readline()
            if line and line[-1:] == self._eol:
                self._parse_and_notify(line)
                self.logger.debug('done with parse')
            else:
                self.logger.debug('did not read a valid line: {}'.format(line))
            try:
                self.logger.debug('try sleep')
                time.sleep(sleep_time - (time.time() - start))
                self.logger.debug('wake up!')
            except ValueError:
                self.logger.debug('sleep error')
                pass

    def _readline(self):
        self.logger.debug('readline')
        return_value = b''
        latest_byte = b''
        while latest_byte != self._eol and not self._kill:
            # TODO: This would be much faster if it read more than one byte
            try:
                latest_byte = self._com.read(1)
            except:
                self.logger.exception("Serial read failed: aborting readline")
                return
            return_value += latest_byte
        self.logger.debug('line read: {}'.format(return_value))
        return return_value

    def _parse_and_notify(self, sdata):
        self.logger.debug('starting block parse')
        data = self._parse_raw_into_dict(sdata)
        signals = []
        if data:
            self.logger.debug('prepare signal')
            try:
                signals.append(Signal({"load": data}))
            except:
                self.logger.exception('error preparing signal')
        self.logger.debug('notifying signal')
        if signals:
            self.notify_signals(signals)
        self.logger.debug('done with block parse')

    def _parse_raw_into_dict(self, sdata):
        self.logger.debug('starting reader parse')
        raw = sdata
        self.logger.debug('raw: {}'.format(raw))
        data = None
        if raw:
            match = self.fmat(raw)
            if not match:
                msg = "Value didn't match: {}".format(raw)
                self.logger.warning(msg)
                return data
            data = match.groupdict()
            for key, value in data.items():
                try:
                    # if it can be converted to an integer, do so
                    data[key] = int(value)
                except (ValueError, TypeError):
                    # otherwise, everything should be a string
                    data[key] = value.decode()
            self.logger.debug("LC in: {} | out: {}".format(raw, data))
        self.logger.debug('done with reader parse')
        return data
