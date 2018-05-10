import time
import threading

class Sequencer(object):

    def __init__(self, midi, queue):
        """
        Construct a sequencer

        midi - Mido MIDI sequence to play
        queue - Queue to dump midi events to as they are sequenced
        """
        self.midi = midi
        self.queue = queue
        self.done_event = threading.Event()

    def sequence(self):
        """
        Start sequencing and block until complete.
        Will dump events into the queue in real-time.
        Blocks until finished.
        """
        self.done_event.clear()
        for event in self.midi:
            time.sleep(event.time)
            self.queue.put(event)

        self.done_event.set()

    def is_done(self):
        return self.done_event.is_set()