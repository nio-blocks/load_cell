
from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.common.discovery import Discoverable, DiscoverableType

from .load_cell import LoadCell


@Discoverable(DiscoverableType.block)
class LoadCell(Block, LoadCell):
    sname = StringProperty(tile="Signal Name", default="cell")
    format = StringProperty(title="Format",
                            default=r'([a-zA-Z])(\w*)(\d{6})(\d{3})(\d{3})')
    address = StringProperty(title="Address", default='/dev/ttyUSB0')
    baud = IntProperty(title="Baud", default=115200)

    def configure(self, context):
        super().configure(context)
        self._cell = LoadCell(self.format.encode(), self.address, self.baud)

    def _parse(self, sdata):
        super()._parse(sdata)
        data = self.data
        name = self.sname
        signals = []
        while data:
            signals.append(Signal({name: data.pop()}))
        self.notify_signals(signals)
