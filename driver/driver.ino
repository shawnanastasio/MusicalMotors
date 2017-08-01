#include <stdint.h>

#include <TimerOne.h>

#define RESOLUTION 18
#define MAX_MOTORS 2
#define MAX_ARGS 5

#define NC_FLAG_ENABLED (1<<0) // Is this NoteCommand enabled?

#define SM_FLAG_ENABLED (1<<0) // Is a motor connected to this pin?
#define SM_FLAG_HIGH    (1<<1) // Is this motor's digital pin set HIGH?

struct NoteCommand {
    uint8_t flags;
    uint16_t delayy;    // Current delay in ticks (microseconds / RESOLUTION)
    uint16_t delayPos; // Current position in period
    uint64_t repeat;    // Number of times to repeat
    uint64_t repeatPos; // Current repeats completed
};

struct StepperMotor {
    int pin;
    uint16_t flags;
    NoteCommand cur_cmd;
};

static volatile StepperMotor motors[MAX_MOTORS];

struct Note {
    int o1;
    int o1b;
    int o1s;
    int o0;
    int o0b;
    int o0s;
};

static Note noteDelay[128];

void tick() {
    // Go through all enabled motors and handle current note
    int i = 0;
    for (i=0; i<MAX_MOTORS; i++) {
        if ((motors[i].flags & SM_FLAG_ENABLED) && (motors[i].cur_cmd.flags & NC_FLAG_ENABLED)) {
            // This motor is connected and has a note to play

            // Increment delayPos
            motors[i].cur_cmd.delayPos += RESOLUTION;
            
            // Check for overflow and toggle pin state
            if (motors[i].cur_cmd.delayPos > motors[i].cur_cmd.delayy) {
                // Toggle motor's pin's state
                motors[i].flags ^= SM_FLAG_HIGH;
                digitalWrite(motors[i].pin, motors[i].flags & SM_FLAG_HIGH);

                // Overflow, reset delayPos and increment repeatPos
                motors[i].cur_cmd.delayPos = 0;
                motors[i].cur_cmd.repeatPos++;

                // If we're done repeating, disable this notecommand
                if (motors[i].cur_cmd.repeatPos > motors[i].cur_cmd.repeat) {
                    //motors[i].cur_cmd.flags &= ~NC_FLAG_ENABLED;
                }
            }
        }
    } 
}

void setup() {
    Serial.begin(115200);
    
    // Install notes
    noteDelay['A'] = {
    .o1 = 1123,
    .o1b = 1190,
    .o1s = 1060,
    };
    
    noteDelay['B'] = {
    .o1 = 1000,
    .o1b = 1060,
    .o1s = 943,
    };
    
    noteDelay['C'] = {
    .o1 = 943,
    .o1b = 1000,
    .o1s = 890,
    };
    
    noteDelay['D'] = {
    .o1 = 840,
    .o1b = 890,
    .o1s = 793,
    };
    
    noteDelay['E'] = {
    .o1 = 747,
    .o1b = 793,
    .o1s = 705,
    };
    
    noteDelay['F'] = {
    .o1 = 705,
    .o1b = 747,
    .o1s = 665,
    };
    
    noteDelay['G'] = {
    .o1 = 629,
    .o1b = 0,
    .o1s = 0,
    .o0 = 1260,
    };


    // Enable motor 0
    pinMode(6, OUTPUT);
    pinMode(5, OUTPUT);
    pinMode(4, OUTPUT);
    digitalWrite(6, LOW);
    digitalWrite(4, LOW);
    motors[0].pin = 5;
    motors[0].flags = SM_FLAG_ENABLED;
#if 0
    // Add a command to play a note 5 times
    motors[0].cur_cmd.flags = NC_FLAG_ENABLED;
    motors[0].cur_cmd.delayy = noteDelay['C'].o1;
    motors[0].cur_cmd.delayPos = 0;
    motors[0].cur_cmd.repeat = 2000;
    motors[0].cur_cmd.repeatPos = 0;
#endif

    // Enable motor 1
    pinMode(8, OUTPUT);
    pinMode(9, OUTPUT);
    pinMode(10, OUTPUT);
    digitalWrite(8, LOW);
    digitalWrite(10, LOW);
    motors[1].pin = 9;
    motors[1].flags = SM_FLAG_ENABLED;
    
#if 0
    // Add a command to play A
    motors[1].cur_cmd.flags = NC_FLAG_ENABLED;
    motors[1].cur_cmd.delayy = noteDelay['E'].o1;
    motors[1].cur_cmd.delayPos = 0;
    motors[1].cur_cmd.repeat = 2000;
    motors[1].cur_cmd.repeatPos = 0;
#endif

    // Install timer
    Timer1.initialize(RESOLUTION);
    Timer1.attachInterrupt(tick);
}


volatile static bool processing_command = false;
static char *args[MAX_ARGS];
static char input_buf[256];
void loop() {
    char *tok;
    int arg_len;
    int motor_idx;
    int i;
    if (Serial.available() && !processing_command) {
        processing_command = false;
        switch (Serial.read()) {
            case 'p':
                // PLAY: usage: p <motor> <noteDelay>
                i = Serial.readBytesUntil('\n', input_buf, 255);
                input_buf[i] = '\0';

                // Load arguments into `args` array
                tok = strtok(input_buf, " ");
                arg_len = 1;
                for (i=0; i<MAX_ARGS; i++) {
                    args[i] = tok;
                    tok = strtok(NULL, " ");
                    if (tok) arg_len++;
                    else break;
                }

                // If the requested motor already has a command, ignore
                motor_idx = atoi(args[0]);
                if (motors[motor_idx].cur_cmd.flags & NC_FLAG_ENABLED) {
                    Serial.println("ERR motor busy");
                    goto done_processing;
                }

                // Set note
                motors[motor_idx].cur_cmd.delayy = atoi(args[1]);
                motors[motor_idx].cur_cmd.delayPos = 0;
                //motors[motor_idx].cur_cmd.repeat = atoi(args[2]);
                //motors[motor_idx].cur_cmd.repeatPos = 0;
                motors[motor_idx].cur_cmd.flags = NC_FLAG_ENABLED;
                Serial.println("OK");
                goto done_processing;

             case 's':
                // STOP: usage: s <motor>
                i = Serial.readBytesUntil('\n', input_buf, 255);
                input_buf[i] = '\0';

                // Load arguments into `args` array
                tok = strtok(input_buf, " ");
                arg_len = 1;
                for (i=0; i<MAX_ARGS; i++) {
                    args[i] = tok;
                    tok = strtok(NULL, " ");
                    if (tok) arg_len++;
                    else break;
                }

                motor_idx = atoi(args[0]);
                
                // Stop currently playing note
                if ((motors[motor_idx].cur_cmd.flags & NC_FLAG_ENABLED) == 0) {
                    Serial.println("ERR motor not busy");
                    goto done_processing;
                }

                motors[motor_idx].cur_cmd.flags &= ~NC_FLAG_ENABLED;
                Serial.println("OK");
                goto done_processing;
                
            done_processing:
                processing_command = false;
                break;
        }
    }
}

