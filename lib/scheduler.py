
class Scheduler(object):
    def __init__(self, motors):
        self.motors = motors
    
    def play(self, event):
        raise RuntimeError("Unimplemented.")

class NopScheduler(Scheduler):
    def play(self, event):
        self.motors[event.channel].play(event)
    
class RoundRobinScheduler(Scheduler):
    def __init__(self, motors):
        Scheduler.__init__(self, motors)
        self.currently_playing = [None for x in range(17)]


    def play(self, event):
        for i in range(len(self.motors)):
            if event.type == "note_off" or (event.type == "note_on" and event.velocity == 0):
                    self.motors[self.currently_playing[event.channel]].play(event)
                    self.currently_playing[event.channel] = None
                    break

            if self.motors[i].current_note == 0:
                # Play to the noting
                self.currently_playing[event.channel] = i
                self.motors[i].play(event)
                
                break