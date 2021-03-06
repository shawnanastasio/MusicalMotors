from .serial_interface import SerialInterface as ser

class MusicalMotor:

    # Default array mapping a MIDI octave and note index to a motor delay
    # Octave 5 Index 0 (MIDI #60) is middle C
    # See: http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/midi_note_numbers_for_octaves.htm
    DEFAULT_MIDI_TO_DELAY = [
        # Octave 0
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 1
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 2
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 3
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 4
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 5 - Contains middle C
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 6
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 7
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 8
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 9
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 10
        [None, None, None, None, None, None, None, None, None, None, None, None],
    ]

    def __init__(self, serial_interface, transpose=False, octaves=None):
        """
        Construct a MusicalMotor

        serial_interface - SerialInterface object to use for communication
        transpose - Should out of range notes be automatically transposed?
        octaves - List of midi octaves to play on this motor
        """
        self.si = serial_interface
        self.transpose = transpose
        self.midi_to_delay = MusicalMotor.DEFAULT_MIDI_TO_DELAY
        self.current_note = 0
        self.octaves = octaves
        self.index = 0

    def get_delay(self, midi):
        octave = midi // 12
        if self.octaves is not None and octave not in self.octaves:
            return None
        index  = midi % 12
        return self.midi_to_delay[octave][index]

    def get_closest_note(self, midi):
        octave = midi // 12
        note = midi % 12
        # List of other octaves that have this note
        other_octaves = []
        for i in range(0, 11, 1):
            if self.octaves is not None and i not in self.octaves:
                continue
            if self.midi_to_delay[i][note] is not None:
                other_octaves.append(i)

        if len(other_octaves) == 0:
            raise ValueError("No octaves contain the requested note!")

        # Find closet octave
        closest = None
        for o in other_octaves:
            if closest is None or abs(octave - o) < closest:
                closest = o

        # Return the note from the found octave
        return self.midi_to_delay[closest][note]
    
    def _send_init_cmd(self):
        """
        Sends an ADD command to inform the controller of the motor and recieve an idx
        """
        raise NotImplementedError()

    def _send_play_cmd(self, delay):
        """
        Sends a command over the Motor's SerialInterface to play a note with the
        specified delay for the specified duration in ms. Must be implemented by subclass.

        delay - motor delay corresponding to requested note
        duration - time in miliseconds to play note for
        """
        raise NotImplementedError()

    def _send_stop_cmd(self):
        """
        Sends a command over the Motor's SerialInterface to stop the current note
        """
        raise NotImplementedError()

    def can_play(self, midi_event):
        if midi_event.type != "note_on" and midi_event.type != "note_off":
            return False

        if self.current_note != 0 and midi_event.type != "note_off":
            if midi_event.note == self.current_note and midi_event.velocity == 0:
                return True
            return False

        return True

    def play(self, midi_event):
        """
        Play the specified MIDI note for the specified duration on this motor.
        Raises ValueError if the requested note does not have a corresponding delay.

        midi - mido MIDI event object
        """

        if midi_event.type != "note_on" and midi_event.type != "note_off":
            raise RuntimeError("Unsupported Note Event!")
            return

        # Handle note_off
        if midi_event.type == "note_off":
            self._send_stop_cmd()
            self.current_note = 0
            return

        # If we're already playing a note, raise an exception
        if self.current_note != 0:
            # See if this event is a velocity=0 event (off) for the current note
            if midi_event.note == self.current_note and midi_event.velocity == 0:
                # Send a stop command
                self._send_stop_cmd()
                self.current_note = 0
                return
            raise RuntimeError("Already playing note!")

        # Get the delay for the given MIDI note
        delay = self.get_delay(midi_event.note)

        # If delay is None and self.transpose is True, find the closest note and use that'
        if delay is None and self.transpose == True:
            delay = self.get_closest_note(midi_event.note)

        if delay is None:
            raise ValueError("Requested note has no corresponding delay!")

        self.current_note = midi_event.note
        self._send_play_cmd(delay)

class StepperMotor(MusicalMotor):
    O4 = {'C': 3790, 'C#': 3580,'D': 3380, 'D#': 3186, 'E': 3008 ,'F': 2840, 'F#': 2679,'G': 2529, 'G#': 2585, 'A': 2250, 'A#': 2126, 'B': 2006}
    O5 = {'C': 1893, 'C#': 1787, 'D': 1686, 'D#': 1591 ,'E': 1501, 'E#': 1416, 'F': 1416,'F#': 1337, 'G#': 1190, 'G': 1260, 'A#': 1060, 'A': 1123, 'B#': 943, 'B': 1000}
    O6 = {'C#': 890, 'C': 943, 'D#': 793, 'D': 840, 'E#': 705, 'E': 747, 'F#': 665, 'F':705, 'G': 629}
    STEPPER_MIDI_TO_DELAY = [
        # Octave 0
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 1
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 2
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 3
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 4
        [O4['C'], O4['C#'], O4['D'], O4['D#'], O4['E'], O4['F'], O4['F#'], O4['G'], O4['G#'], O4['A'], O4['A#'], O4['B']],
        # Octave 5 - Contains middle C
        [O5['C'], O5['C#'], O5['D'], O5['D#'], O5['E'], O5['F'], O5['F#'], O5['G'], O5['G#'], O5['A'], O5['A#'], O5['B']],
        # Octave 6
        [O6['C'], O6['C#'], O6['D'], O6['D#'], O6['E'], O6['F'], O6['F#'], O6['G'], None, None, None, None],
        # Octave 7
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 8
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 9
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 10
        [None, None, None, None, None, None, None, None, None, None, None, None],
    ]

    def __init__(self, serial_interface, step_pin, transpose=False, octaves=None):
        MusicalMotor.__init__(self, serial_interface, transpose=transpose, octaves=octaves)
        self.midi_to_delay = self.STEPPER_MIDI_TO_DELAY
        self.step_pin = step_pin
        self.index = self._send_init_cmd()

    def _send_init_cmd(self):
        return self.si.add(self.step_pin, 0, ser.MM_FLAG_ENABLED)

    def _send_play_cmd(self, delay):
        self.si.play(self.index, delay)

    def _send_stop_cmd(self):
        self.si.stop(self.index)


class FloppyDrive(MusicalMotor):
    FLOPPY_MIDI_TO_DELAY = [
        # Octave 0
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 1
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 2
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 3
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 4
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 5 - Contains middle C
        [7644, 7215, 6810, 6428, 6067, 5727, 5405, 5102, 4815, 4545, 4290, 4049],
        # Octave 6
        [3822, 3609, 3405, 3214, 3033, 2863, 2702, 2551, 2408, 2272, 2145, 2024],
        # Octave 7
        [1911, 1804, 1702, 1607, 1517, 1431, 1351, 1275, 1204, 1136, 1072, 1012],
        # Octave 8
        [955, 902, 851, 803, 758, 716, 675, 638, 602, 568, 536, 506],
        # Octave 9
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 10
        [None, None, None, None, None, None, None, None, None, None, None, None],                
    ]

    def __init__(self, serial_interface, step_pin, dir_pin, transpose=False, octaves=None):
        MusicalMotor.__init__(self, serial_interface, transpose=transpose, octaves=octaves)
        self.midi_to_delay = self.FLOPPY_MIDI_TO_DELAY
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.index = self._send_init_cmd()
        
        # Send a reset command to this motor
        self._send_reset_cmd()

    def _send_init_cmd(self):
        return self.si.add(self.step_pin, self.dir_pin, ser.MM_FLAG_ENABLED | ser.MM_FLAG_FLOPPY)
    
    def _send_reset_cmd(self):
        self.si.reset(self.index)
    
    def _send_play_cmd(self, delay):
        self.si.play(self.index, delay)

    def _send_stop_cmd(self):
        self.si.stop(self.index) 

class DummyMotor(MusicalMotor):
    def __init__(self):
        pass

    def _send_init_cmd(self):
        return 0
    
    def _send_reset_cmd(self):
        pass
    
    def _send_play_cmd(self, delay):
        pass

    def _send_stop_cmd(self):
        pass
