#!/usr/bin/env python3

import signal
import sys
import time
import mido
import gc
import lib.musical_motor as mm
import lib.scheduler as sched
from lib.serial_interface import SerialInterface
from lib.config import Config
from lib.sleeputils import precisesleep

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

    # Instantiate scheduler
    scheduler = sched.NopScheduler(config.motors)

    motors_len = len(config.motors)
    start = time.time()
    for msg in mid:
        precisesleep(msg.time)

        try:
            if msg.is_meta:
                continue

            if motors_len - 1 < msg.channel:
                continue

            scheduler.play(msg)
        except Exception as e:
            print("Error: " + str(e))
            pass


    end = time.time()
    print("Played song in {} seconds".format(end - start))

    # Stop all motors
    for motor in motors:
        try:
            motor._send_stop_cmd()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
