"""
Provides a serial interface for talking to the arduino
"""
import serial
import time
import random
import sys
import configparser


"""
SerialInterface for issuing commands to the arduino
Supported commands:
  - CMD_PLAY: Play a note on the specified stepper motor
"""
class SerialInterface(object):
    CMD_PLAY = "p"
    def __init__(self, port, baud, timeout=1):
        # Establish a serial connection
        self.s = serial.Serial(port, baud, timeout=timeout)

        # Wait for arduino to boot up
        time.sleep(2)

    # motor - motor index to play note on
    # note_delay - step delay of note to play
    # duration - duration in ms to play note for
    # Returns tuple (bool success, str response from arduino)
    def play(self, motor, note_delay, duration):
        # Send a play command to the requested motor
        self.s.write(bytes("%s %d %d %d \n" % (self.CMD_PLAY, motor, note_delay, 500*duration/note_delay), "UTF-8"))

        # Recieve the full response
        resp = self.s.readline()
        #while not "ERR" in resp and not "OK" in resp:
        #    resp += self.s.readline()

        if not bytes("ERR", "UTF-8") in resp:
            return (True, resp.rstrip())
        else:
            return (False, resp.rstrip())
