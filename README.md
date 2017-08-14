LoadCell
========
Read from load cells over serial.

Properties
----------
- **address**: Serial port to read from.
- **baud**: Baud rate of serial port.
- **format**: Regular expression for parsing serial data stream.

Inputs
------

Outputs
-------
- **default**: Outputs a signal with the attribute `load` for each load cell read.

Commands
--------

Dependencies
------------
-   [pyserial](https://pypi.python.org/pypi/pyserial)
