#!/usr/bin/env python3

import signal
import sys
import mido
import lib.note_database as nd
import lib.musicalmotor as mm
from lib.serial_interface import SerialInterface
from lib.config import Config

motors = []

def quit_handler(signal, frame):
    # Stop all motors
    try:
        for m in motors:
            m._send_stop_cmd()
    except:
        pass

    sys.exit(0)
    

def main():
    signal.signal(signal.SIGINT, quit_handler)
    
    # Get MIDI file from argument 1
    if len(sys.argv) != 2:
        print("Usage: {} <song.midi>".format(sys.argv[0]))
        return 1

    # Read config file
    config = Config()

    # Read the midi
    mid = mido.MidiFile(sys.argv[1])

    # Initalize serial interface
    si = SerialInterface(config.arduino_port, config.baud)

    # Initalize motors
    motors.append(mm.StepperMotor(si, 0, transpose=True))
    motors.append(mm.StepperMotor(si, 1, transpose=True))
    

    # Play each event in the midi
    for msg in mid.play():
        if msg.type == "note_off" and (msg.channel == 0 or msg.channel == 1):
            print(msg)
        try:
            # See if we have a motor for this channel
            if len(motors)-1 < msg.channel:
                #print("No motor for channel {}!".format(msg.channel))
                continue
            
            # If the corresponding motor is free, use that
            if motors[msg.channel].can_play(msg):
                motors[msg.channel].play(msg)
            else:
                # The motor isn't able to play this, try all the others
                for i in range(0, len(motors), 1):
                    if i != msg.channel and motors[msg.channel].can_play(msg):
                        motors.play(msg)
                        break 
        except Exception as e:
            print("err:", e)
            #return 1

    # Stop all motors
    for motor in motors:
        try:
            motor._send_stop_cmd()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
