MusicalMotors
=============
MusicalMotors is a set of tools to play MIDI files on stepper motors and floppy drives.

Requirements
------------
* Python 3
* `configparser`, `pyserial` from `pip`

Usage
-----
Copy `config.ini.example` to `config.ini` and fill in your Arduino's serial information.
TODO

Files
-----

* driver.ino - Arduino driver to recieve serial commands and control stepper motors

* serial_interface.py - WIP python script to send serial commands to Arduino stepper driver. Will eventually integrate with a MIDI sequencer
