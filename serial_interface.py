"""
Provides a serial interface for talking to the arduino
"""
import serial
import time
import random
import sys

ARDUINO_PORT = "/dev/cu.usbmodem1441" # Path to serial port
BAUD = 9600

OCTAVE_ONE = {'A': 1123, 'B': 1000, 'C': 943, 'G': 1240}

"""
SerialInterface for issuing commands to the arduino
Supported commands:
  - CMD_READ: Read a byte from a ring buffer on the arduino
  - CMD_WRITE: Write a byte to a ring buffer on the arduino
"""
class SerialInterface(object):
    CMD_PLAY = "p"
    def __init__(self, port, baud, timeout=1):
        # Establish a serial connection
        self.s = serial.Serial(port, baud, timeout=timeout)

        # Wait for arduino to boot up
        time.sleep(2)

    # Returns tuple (bool success, str response from arduino)
    def play(self, motor, note_delay, duration):
        # Send a read command for the requested ringbuf
        self.s.write("%s %d %d %d \n" % (self.CMD_PLAY, motor, note_delay, duration))

        # Recieve the full response
        resp = self.s.readline()
        #while not "ERR" in resp and not "OK" in resp:
        #    resp += self.s.readline()

        print resp
        if not "ERR" in resp:
            return (True, resp.rstrip())
        else:
            return (False, resp.rstrip())


def main():
    si = SerialInterface(ARDUINO_PORT, BAUD)

    #si.play(0, OCTAVE_ONE['B'], 1000)
    #time.sleep(1)
    #si.play(0, OCTAVE_ONE['A'], 1000)
    #time.sleep(1.2)
    si.play(0, OCTAVE_ONE['G'], 10000)
    #delay
    #si.play(0, OCTAVE_ONE['B'], 1000)
    #si.play(0, OCTAVE_ONE['A'], 1000)
    #si.play(0, OCTAVE_ONE['G'], 1000)
    #delay

if __name__ == "__main__":
    main()


    
    