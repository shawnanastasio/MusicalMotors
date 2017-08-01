# Return the midi note index for the given octave and note
# see http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/midi_note_numbers_for_octaves.htm
# octave - octave (0-10)
# note - note (0-11)
def get_midi_index(octave, note):
    return octave*12 + note

def get_closest_note(arr, octave, note):
    # List of other octaves that have this note
    other_octaves = []
    for i in range(0, 10, 1):
        if arr[i][note] is not None:
            other_octaves.append(i)

    # Find closet octave
    closest = -1
    for o in other_octaves:
        if abs(octave - o) < closest or closest == -1:
            closest = o

    # Return the note from the found octave
    return other_octaves[o][note]

O1 = {'G#': 1190, 'G': 1260, 'A#': 1060, 'A': 1123, 'B#': 943, 'B': 1000, 'C#': 890, 'C': 943, 'D#': 793, 'D': 840, 'E#': 705, 'E': 747, 'F#': 665, 'F':705}
O2 = {'G': 629}

STEPPER_MIDI_TO_DELAY = \
[
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
