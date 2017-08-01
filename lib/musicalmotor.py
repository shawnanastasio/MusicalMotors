
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

    def __init__(self, serial_interface, index, transpose=False):
        self.si = serial_interface
        self.index = index
        self.transpose = transpose
        self.midi_to_delay = MusicalMotor.DEFAULT_MIDI_TO_DELAY

    def get_delay(self, midi):
        octave = midi // 12
        index  = midi % 12
        return self.midi_to_delay[octave][index]

    def get_closest_note(self, midi):
        octave = midi // 12
        note = midi % 12
        # List of other octaves that have this note
        other_octaves = []
        for i in range(0, 10, 1):
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

    def _send_play_cmd(self, delay, duration):
        """
        Sends a command over the Motor's SerialInterface to play a note with the
        specified delay for the specified duration in ms. Must be implemented by subclass.

        delay - motor delay corresponding to requested note
        duration - time in miliseconds to play note for
        """
        raise NotImplementedError()

    def play(self, midi, duration):
        """
        Play the specified MIDI note for the specified duration on this motor.
        Raises ValueError if the requested note does not have a corresponding delay.

        midi - MIDI note index number
        duration - duration in ms to play note for
        """

        # Get the delay for the given MIDI note
        delay = self.get_delay(midi)

        # If delay is None and self.transpose is True, find the closest note and use that'
        if delay is None and self.transpose == True:
            delay = self.get_closest_note(midi)

        if delay is None:
            raise ValueError("Requested note has no corresponding delay!")

        self._send_play_cmd(delay, duration)

class StepperMotor(MusicalMotor):
    O1 = {'G#': 1190, 'G': 1260, 'A#': 1060, 'A': 1123, 'B#': 943, 'B': 1000, 'C#': 890, 'C': 943, 'D#': 793, 'D': 840, 'E#': 705, 'E': 747, 'F#': 665, 'F':705}
    O2 = {'G': 629}
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
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 5 - Contains middle C
        [O1['C'], O1['C#'], O1['D'], O1['D#'], O1['E'], O1['F'], O1['F#'], O1['G'], O1['G#'], O1['A'], O1['A#'], O1['B']],
        # Octave 6
        [None, None, None, None, None, None, None, O2['G'], None, None, None, None],
        # Octave 7
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 8
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 9
        [None, None, None, None, None, None, None, None, None, None, None, None],
        # Octave 10
        [None, None, None, None, None, None, None, None, None, None, None, None],
    ]

    def __init__(self, serial_interface, index, transpose=False):
        MusicalMotor.__init__(self, serial_interface, index, transpose=transpose)
        print(self.transpose, "KEK")
        self.midi_to_delay = StepperMotor.STEPPER_MIDI_TO_DELAY

    def _send_play_cmd(self, delay, duration):
        self.s.play(motor, note_delay, duration)