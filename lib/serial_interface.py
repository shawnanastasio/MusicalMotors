"""
Provides a serial interface for talking to the arduino
"""
import serial
import time
import random
import sys
import configparser

class SerialException(Exception):
    pass

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
    CMD_WIPE = 3
    CMD_ADD = 4

    ERR_SUCCESS = 0
    ERR_MOTORBUSY = 1
    ERR_BADMOTOR = 2

    MM_FLAG_ENABLED = 0x1
    MM_FLAG_FLOPPY = 0x8
    MM_FLAG_NORESET = 0x10

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

        self.wipe()

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
        try:
            resp = self.s.read()[0]
        except Exception:
            raise SerialException("Arduino didn't respond to command! Check serial port configuration and make sure it is programmed.")

        if resp != SerialInterface.ERR_SUCCESS:
            raise SerialException("Arduino responded with an error! %s" % (SerialInterface.ERRORS[resp]))

    def wipe(self):
        """
        Wipe all installed floppy drives
        """
        self.s.write(bytes([SerialInterface.CMD_WIPE]))

        try:
            resp = self.s.read()[0]
        except Exception:
            raise SerialException("Arduino didn't respond to command! Check serial port configuration and make sure it is programmed.")
  
        if resp != SerialInterface.ERR_SUCCESS:
            raise SerialException("Arduino responded with an error! %s" % (SerialInterface.ERRORS[resp]))

    def add(self, step_pin, dir_pin, flags):
        """
        Add a motor

        step_pin - Arduino pin connected to STEP
        dir_pin - Arduino pin connected to DIRECTION
        flags - MM_FLAG_* bitfield

        Returns motor index on success
        """
        self.s.write(bytes([SerialInterface.CMD_ADD, step_pin & 0xFF, dir_pin & 0xFF, flags & 0xFF]))
        
        try:
            resp = self.s.read()[0]
        except Exception:
            raise SerialException("Arduino didn't respond to command! Check serial port configuration and make sure it is programmed.")
 
        if resp != SerialInterface.ERR_SUCCESS:
            raise SerialException("Arduino responded with an error! %s" % (SerialInterface.ERRORS[resp]))

        # If we got here, the Arduino is going to send back a motor idx
        return self.s.read()[0]

