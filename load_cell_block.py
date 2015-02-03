
from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.common.discovery import Discoverable, DiscoverableType

from .load_cell import LoadCellReader


@Discoverable(DiscoverableType.block)
class LoadCell(LoadCellReader, Block):
    sname = StringProperty(tile="Signal Name", default="load")
    format = StringProperty(title="Format",
                            default=r'(?P<token>[a-zA-Z])(?P<id>\w*)'
                            r'(?P<weight>\d{6})(?P<temperature>\d{3})'
                            r'(?P<battery>\d{3})')
    address = StringProperty(title="Address", default='/dev/ttyUSB0')
    baud = IntProperty(title="Baud", default=115200)

    def __init__(self):
        Block.__init__(self)

    def configure(self, context):
        Block.configure(self, context)

    def start(self):
        Block.start(self)
        LoadCellReader.__init__(
            self, self.format.encode(), self.address, self.baud,
            log=self._logger)

    def _parse(self, sdata):
        LoadCellReader._parse(self, sdata)
        data = self.data
        name = self.sname
        signals = []
        while data:
            signals.append(Signal({name: data.pop()}))
        if signals:
            self.notify_signals(signals)
