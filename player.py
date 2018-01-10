#!/usr/bin/env python3

import signal
import sys
import time
import mido
import gc
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
    gc.disable()

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
    motors.append(mm.FloppyDrive(si, 0, transpose=True, octaves=[5,6]))
    #motors.append(mm.FloppyDrive(si, 1, transpose=True, octaves=[5,6]))
    #motors.append(mm.FloppyDrive(si, 2, transpose=True, octaves=[5,6]))
    #motors.append(mm.FloppyDrive(si, 3, transpose=True, octaves=[5,6]))


    messages = []
    motors_len = len(motors)
    last_delta = 0
    for msg in mid:
        time.sleep(msg.time)
        #messages.append(msg)
        if msg.is_meta:
            continue

        if motors_len - 1 < msg.channel:
            continue
        
        try:
            start_time = time.perf_counter()
            motors[msg.channel].play(msg)
        except Exception as e:
            print(e)
            pass
        
        last_delta = round(time.perf_counter() - start_time, 3)

    return
    # Play each event in the midi
    last_delta = 0
    for i in range(0, len(messages), 1):
        #print("last note took: {} seconds".format(last_delta))
        #print("sleeping for: {} seconds".format(messages[i].time))
        time.sleep(max(messages[i].time - last_delta, 0))
        if round(messages[i].time - last_delta, 2) < 0:
            print("ERROR: delta took longer than note delay! {} sec".format(messages[i].time - last_delta))
            sys.exit(0)

        
        last_delta = 0
        msg = messages[i]
        if (msg.type == "note_off" or msg.type == "note_on") and (msg.channel == 0 or msg.channel == 1):
            print(msg)
        try:
            # See if we have a motor for this channel
            if len(motors)-1 < msg.channel:
                #print("No motor for channel {}!".format(msg.channel))
                continue

            start_time = time.perf_counter()
            # If the corresponding motor is free, use that
            motors[msg.channel].play(msg)
            end_time = time.perf_counter()
            last_delta = end_time - start_time

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
