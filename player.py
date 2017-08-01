#!/usr/bin/env python3

import sys
import mido
import lib.note_database as nd
import lib.musicalmotor as mm
from lib.serial_interface import SerialInterface
from lib.config import Config

def main():
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
    motors = []
    motors.append(mm.StepperMotor(None, 0, transpose=True))
    motors.append(mm.StepperMotor(None, 0, transpose=True))

    # Play each event in the midi
    for msg in mid.play():
        # Handle "note_on" messages (play a note)
        if msg.type == "note_on" and msg.note is not None:
            # See if we have a motor for this channel
            if len(motors)-1 < msg.channel:
                print("No motor for channel {}!".format(msg.channel))
            else:
                print("Playing note {}!".format(msg.note))
                motors[msg.channel].play(msg.note, msg.time * 1000)


if __name__ == "__main__":
    sys.exit(main())
