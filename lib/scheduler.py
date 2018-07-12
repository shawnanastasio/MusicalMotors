
class Scheduler(object):
    def __init__(self, motor_map):
        """
        motor_map: list [idx=midi channel, val=list of motor objects]
        """
        self.motor_map = motor_map
    
    def play(self, event):
        raise RuntimeError("Unimplemented.")

class NopScheduler(Scheduler):
    def play(self, event):
        #self.motors[event.channel].play(event)
        if len(self.motor_map[event.channel]) > 0:
            # Motor map has associate motor(s) for this channel,
            # Play the event on all of them
            for m in self.motor_map[event.channel]:
                m.play(event)
    
class RoundRobinScheduler(Scheduler):
    def __init__(self, motor_map):
        Scheduler.__init__(self, motor_map)
        # Generate a raw list of motors and ignore the motor map
        self.motors = sum(self.motor_map, [])
        self.currently_playing = [None for x in range(16)]


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
