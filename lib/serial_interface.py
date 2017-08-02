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
    CMD_PLAY = "p"
    CMD_STOP = "s"
    CMD_RESET = "r"
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
        duration - duration in ms to play note for
        """
        # Send a play command to the requested motor
        self.s.write(bytes("%s %d %d \n" % (self.CMD_PLAY, motor, note_delay), "UTF-8"))

        # Recieve the full response
        resp = self.s.readline()
        #while not "ERR" in resp and not "OK" in resp:
        #    resp += self.s.readline()

        if bytes("ERR", "UTF-8") in resp:
            raise RuntimeError("Arduino responded with an error! %s" % (resp.decode("UTF-8")))

    def stop(self, motor):
        """
        Stop playing a note on the specified motor

        motor - motor index to stop
        """
        self.s.write(bytes("%s %d \n" % (self.CMD_STOP, motor), "UTF-8"))

        resp = self.s.readline()

        if bytes("ERR", "UTF-8") in resp:
            raise RuntimeError("Arduino responded with an error! %s" % (resp.decode("UTF-8")))
    
    def reset(self, motor):
        """
        Reset the specified floppy drive

        motor - motor index of floppy drive to stop
        """
        self.s.write(bytes("%s %d \n" % (self.CMD_RESET, motor), "UTF-8"))

        resp = self.s.readline()

        if bytes("ERR", "UTF-8") in resp:
            raise RuntimeError("Arduino responded with an error! %s" % (resp.decode("UTF-8")))