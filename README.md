LoadCell
========

Read from load cells over serial

Properties
--------------

-   **address** (type:string): Serial port to read from
-   **baud** (type:int): Baud rate of serial port
-   **format** (type:string): Regular expression for parsing serial data stream

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
