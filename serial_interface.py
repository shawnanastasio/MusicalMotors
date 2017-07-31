"""
Provides a serial interface for talking to the arduino
"""
import serial
import time
import random
import sys
import configparser

CONFIG_PATH = "config.ini" # Path to configuration file

ARDUINO_PORT = None # Path to serial port
BAUD = None         # Baudrate of serial port

OCTAVE_ONE = {'G': 1260, 'A': 1123, 'B': 1000, 'C': 943, 'D': 840, 'E': 747, 'F': 705}
OCTAVE_ONESHARP = {'G': 1190, 'A': 1060, 'B': 943, 'C': 890, 'D': 793, 'E': 705, 'F': 665}
OCTAVE_TWO = {'G': 629}

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
        self.s.write("%s %d %d %d \n" % (self.CMD_PLAY, motor, note_delay, 500*duration/note_delay))

        # Recieve the full response
        resp = self.s.readline()
        #while not "ERR" in resp and not "OK" in resp:
        #    resp += self.s.readline()

        if not "ERR" in resp:
            return (True, resp.rstrip())
        else:
            return (False, resp.rstrip())


def main():
    global ARDUINO_PORT, BAUD
    # Read in ARDUINO_PORT and BAUD from config.ini file
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    ARDUINO_PORT = config.get("Arduino", "SerialPort")
    BAUD = config.get("Arduino", "Baudrate")

    si = SerialInterface(ARDUINO_PORT, BAUD)

    #si.play(0, OCTAVE_ONE['B'], 1000)
    #time.sleep(1)
    si.play(1, OCTAVE_ONE['B'], 1000)
    #time.sleep(1.2)
    si.play(0, OCTAVE_ONE['A'], 1000)
    #delay
    #si.play(0, OCTAVE_ONE['B'], 1000)
    #si.play(0, OCTAVE_ONE['A'], 1000)
    #si.play(0, OCTAVE_ONE['G'], 1000)
    #delay

if __name__ == "__main__":
    main()
