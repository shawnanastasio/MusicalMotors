"""
Provides a serial interface for talking to the arduino
"""
import serial
import time
import random
import sys
import configparser


class SerialInterface(object):
    """
    SerialInterface for issuing commands to the arduino.
    Supported commands:
    - CMD_PLAY: Play a note on the specified stepper motor
    - CMD_STOP: Stop a playing note
    - CMD_RESET: Reset the specified floppy drive
    """
    CMD_PLAY = 0
    CMD_STOP = 1
    CMD_RESET = 2

    ERR_SUCCESS = 0

    ERRORS = [
        "Success",
        "Motor busy",
        "Bad motor",
    ]

    def __init__(self, port, baud, timeout=1):
        # Establish a serial connection
        self.s = serial.Serial(port, baud, timeout=timeout)

        # Wait for arduino to boot up
        time.sleep(2)

    def play(self, motor, note_delay):
        """
        Play a note on the specified motor

        motor - motor index to play note on
        note_delay - step delay of note to play
        """
        # Send a play command to the requested motor
        self.s.write(bytes([SerialInterface.CMD_PLAY, motor, note_delay >> 8, note_delay & 0xFF]))

    def stop(self, motor):
        """
        Stop playing a note on the specified motor

        motor - motor index to stop
        """
        self.s.write(bytes([SerialInterface.CMD_STOP, motor]))

    def reset(self, motor):
        """
        Reset the specified floppy drive

        motor - motor index of floppy drive to stop
        """
        self.s.write(bytes([SerialInterface.CMD_RESET, motor]))

        # Recieve the response
        resp = self.s.read()[0]

        if resp != SerialInterface.ERR_SUCCESS:
            raise RuntimeError("Arduino responded with an error! %s" % (SerialInterface.ERRORS[resp]))