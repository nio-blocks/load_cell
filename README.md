LoadCell
==========

Read from load cells over serial

Properties
--------------

-   address (str): Serial port to read from
-   baud (int): Baud rate of serial port
-   format (string): Regular expression for parsing serial data stream
-   sname (string): Name of the attribute to put on output signal

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
Outputs a signal with the attribute *sname* for each load cell read.
