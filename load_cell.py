import re
from collections import deque
from threading import Lock

from .oserial import Serial


class LoadCellReader(Serial):
    def __init__(self, fmat, port='/dev/ttyUSB0', baud=38400, log=None):
        self.log = log
        self.fmat = re.compile(fmat).match
        self._lock = Lock()
        self.data = deque()
        super().__init__(port, baud, 0.05, b'\r')

    def _parse(self, sdata):
        df = self.fmat
        raw = self.raw
        mydata = self.data
        super()._parse(sdata)
        with self._lock:
            while raw:
                value = self.raw.pop()
                match = df(value)
                if not match:
                    msg = "Value didn't match: {}".format(value)
                    if self.log is not None:
                        self.log.warning(msg)
                    continue
                data = match.groupdict()
                for key, value in data.items():
                    try:
                        data[key] = int(value)
                    except (ValueError, TypeError):
                        pass
                mydata.appendleft(data)

    def read(self):
        '''Return a list of all data since last read'''
        mydata = self.data
        data = []
        while mydata:
            data.append(mydata.pop())
        return data


def _test():
    from pprint import pprint
    format = (rb'(?P<token>[a-zA-Z])(?P<id>\w*)'
              rb'(?P<weight>\d{6})(?P<temperature>\d{3})'
              rb'(?P<battery>\d{3})')

    data = (b'B035851000197104100\rA035848000000104100\rB035851000197104100\r' +
            b'A035848000104104100\rB035851000197104100\r')
    cell = LoadCellReader(format, None)
    cell._parse(data)
    pprint(list(cell.data))

if __name__ == '__main__':
    _test()

