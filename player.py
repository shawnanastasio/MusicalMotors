#!/usr/bin/env python3

import signal
import sys
import time
import mido
import gc
import argparse
import traceback
import lib.musical_motor as mm
import lib.scheduler as sched
from lib.serial_interface import SerialInterface
from lib.config import Config, SongConfig
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

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Play a MIDI file on a connected MusicalMotor driver")
    parser.add_argument("path", help="Path to MIDI file to play, or the songconfig file if -s is specified", type=str)
    parser.add_argument("-c", "--config", help="Specify a custom configuration file path", type=str)
    parser.add_argument("-s", "--songconfig", help="Treat `path` as a songconfig file instead of a raw MIDI file", action="store_true")
    args = parser.parse_args()
 
    # Read config file
    if args.config:
        config = Config(config_path=args.config)
    else:
        config = Config()

    # Read in the SongConfig, or generate a default one
    if args.songconfig:
        sc = SongConfig.from_file(config, args.path)
    else:
        sc = SongConfig(config, args.path)

    
    # Begin playing MIDI file
    start = time.time()
    for msg in sc.midi:
        precisesleep(msg.time)

        try:
            if msg.is_meta:
                continue

            sc.scheduler.play(msg)
        except Exception as e:
            #traceback.print_exc()
            print("Error: " + str(e))
            pass


    end = time.time()
    print("Played song in {} seconds".format(end - start))

    # Stop all motors
    for motor in config.motors:
        try:
            motor._send_stop_cmd()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
