
class LoadCell():
    def __init__(self, port='/dev/ttyUSB0', baud=38400):
        self._port = Serial(port, baud, 0.05, b'\r')

    def read(self):
        data = []
        raw = self._port.raw
        df = DATA_FORMAT
        while raw:
            value = raw.pop()
            match = df(value)
            if not match:
                print("Value didn't match", value)
                continue
            ind, serial, weight, unk = match.groups()
            data.append({
                'id': ind,
                'serial': serial,
                'weight': weight,
                'unknown': unk
            })
        return data









