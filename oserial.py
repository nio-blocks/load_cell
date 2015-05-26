import time
from collections import deque
from threading import Thread
try:
    import serial
except ImportError:
    print("Could not import Serial -- debug mode only")


class Serial(object):
    def __init__(self, port='/dev/ttyAMA0', baud=38400, timeout=0.05,
                 eol=b'\r', log=None):
        self._kill = False
        self.eol = eol
        self.log = log

        self._unparsed = b''
        self.raw = deque()

        if not port:
            self._com = None
        else:
            # Setup the com port
            self._com = serial.Serial(port, baud)
            self._com.timeout = 0.15
            self._com.readall()  # flush buffer
            self._com.timeout = timeout

            # Start the reading thread
            self._thread = Thread(target=self._read_thread)
            self._thread.daemon = True
            self._thread.start()

    def _write(self, command):
        command = encode(command)
        self._com.write(command + b'\r')

    def _read(self):
        self.log.debug('read')
        return self._com.readall()

    def _parse(self, data):
        self.log.debug('starting serial parse')
        data = data.split(self.eol)
        if len(data) == 1:
            self._unparsed = data[0]
            self.log.debug('done with serial parse')
            return
        data[0] = b''.join((self._unparsed, data[0]))
        self._unparsed = data.pop()
        self.raw.extendleft(data)
        self.log.debug('done with serial parse')

    def _read_thread(self):
        sleep_time = 0.2
        time.sleep(sleep_time)
        while not self._kill:
            self.log.debug('read_thread loop')
            start = time.time()
            self.log.debug('start time'.format(start))
            self._parse(self._read())
            self.log.debug('done with parse')
            try:
                self.log.debug('try sleep')
                time.sleep(sleep_time - (time.time() - start))
                self.log.debug('wake up!')
            except ValueError:
                self.log.debug('sleep error')
                pass

    def __del__(self):
        self._kill = True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='parse serial output and print to file and to terminal')
    parser.add_argument('port', help='Port to connect to')
    parser.add_argument('file', help='File path to output to', default='minicom.log')
    parser.add_argument('-b', '--baud', default=115200, type=int, help='baud rate')
    args = parser.parse_args()

    print("Connecting to port {} at baud {} and outputing to file {}".format(args.port, args.baud, args.file))
    port = Serial(args.port, args.baud, timeout=1)

    with open(args.file, 'a') as f:
        while True:
            while port.raw:
                out = port.raw.pop()
                print(repr(out))
                f.write('{:30}'.format(time.ctime()) + repr(out) + '\n')
                f.flush()
            time.sleep(0.1)
