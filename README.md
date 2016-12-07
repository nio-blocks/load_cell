LoadCell
========

Read from load cells over serial

Properties
--------------

-   **address** (str): Serial port to read from
-   **baud** (int): Baud rate of serial port
-   **format** (str): Regular expression for parsing serial data stream

Dependencies
----------------

-   [pyserial](https://pypi.python.org/pypi/pyserial)

Commands
----------------
None

Input
-------
None

Output
---------
Outputs a signal with the attribute `load` for each load cell read.
