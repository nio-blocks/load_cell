import re
from datetime import datetime
import time
from collections import deque
from threading import Lock

from .oserial import Serial

DATA_FORMAT =


class LoadCell(Serial):
    def __init__(self, format, port='/dev/ttyUSB0', baud=38400, log=None):
        self.log = log
        re.compile(format).match
        self._lock = Lock()
        self.data = deque()
        super().__init__(port, baud, 0.05, b'\r')

    def _parse(self, sdata):
        df = DATA_FORMAT
        raw = self.raw
        mydata = self.data
        super()._parse(sdata)
        timestamp = datetime.utcnow()
        with self._lock:
            while raw:
                value = self.raw.pop()
                match = df(value)
                if self.log is not None:
                    self.log.warning("Value didn't match: {}".format(value))
                    continue
                token, id, weight, temp, bat = match.groups()
                mydata.appendleft({
                    'timestamp': timestamp,
                    'token': token.decode(),
                    'id': id.decode(),
                    'weight': int(weight),
                    'temperature': int(temp),
                    'battery': int(bat)
                })

    def read(self):
        '''Return a list of all data since last read'''
        mydata = self.data
        data = []
        while mydata:
            data.append(mydata.pop())
        return data

def _test():
    from pprint import pprint
    format = rb'([a-zA-Z])(\w*)(\d{6})(\d{3})(\d{3})'
    data = (b'B035851000197104100\rA035848000000104100\rB035851000197104100\r' +
            b'A035848000104104100\rB035851000197104100\r')
    cell = LoadCell(format, None)
    cell._parse(data)
    pprint(list(cell.data))

if __name__ == '__main__':
    _test()

