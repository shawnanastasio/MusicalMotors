#include <stdint.h>

#include <TimerOne.h>

/* PROGRAM CONSTANTS */
#define RESOLUTION 20  // Note resolution in microseconds. tick() is called at this interval
#define MAX_MOTORS 10  // Maximum number of motors supported
#define MAX_ARGS 5     // Maximum number of serial command arguments. Don't change this.

#define FLOPPY_DEFAULT_MAX 160 // Default max head position for a floppy drive. 160 for 3.5".

/* NOTECOMMAND FLAGS */
#define NC_FLAG_ENABLED (1<<0) // Is this NoteCommand enabled?

/* MUSICALMOTOR FLAGS */
#define MM_FLAG_ENABLED (1<<0) // Is a motor connected to this pin?
#define MM_FLAG_HIGH1   (1<<1) // Is this motor's pin1 set HIGH?
#define MM_FLAG_HIGH2   (1<<2) // Is this motor's pin2 set HIGH? (floppy only)
#define MM_FLAG_FLOPPY  (1<<3) // Is this motor a floppy drive?

struct NoteCommand {
    uint8_t delay;     // Current delay in ticks (microseconds / RESOLUTION)
    uint8_t delayPos;  // Current position in period
    uint8_t flags;
};

struct MusicalMotor {
    int pin1;          // Primary pin for steppers, STEP for floppies
    int pin2;          // Unused for steppers, DIRECTION for floppies
    uint8_t flags;
    uint8_t floppyMax; // Maximum head position (only used on floppy)
    uint8_t floppyCur; // Current head position (only used on floppy)
    NoteCommand curCmd;
};

static volatile MusicalMotor motors[MAX_MOTORS];


void tick() {
    // Go through all enabled motors and handle current note
    int i = 0;
    for (i=0; i<MAX_MOTORS; i++) {
        if ((motors[i].flags & MM_FLAG_ENABLED) && (motors[i].curCmd.flags & NC_FLAG_ENABLED)) {
            // This motor is connected and has a note to play

            // If this motor is a floppy drive handle DIRECTION swapping
            if (motors[i].flags & MM_FLAG_FLOPPY) {
                motors[i].floppyCur++;
                if (motors[i].floppyCur >= motors[i].floppyMax) {
                    motors[i].flags ^= MM_FLAG_HIGH1;
                    digitalWrite(motors[i].pin2, motors[i].flags & MM_FLAG_HIGH2);
                    motors[i].floppyCur = 0;
                }
            }

            // Increment delayPos
            motors[i].curCmd.delayPos++;
            
            // Check for overflow and toggle pin state
            if (motors[i].curCmd.delayPos > motors[i].curCmd.delay) {
                // Toggle motor's pin's state
                motors[i].flags ^= MM_FLAG_HIGH1;
                digitalWrite(motors[i].pin1, motors[i].flags & MM_FLAG_HIGH1);

                // Overflow, reset delayPos and increment repeatPos
                motors[i].curCmd.delayPos = 0;
            }
        }
    } 
}

void setup() {
    Serial.begin(115200);

    // Enable motor 0 (Stepper)
    pinMode(6, OUTPUT);
    pinMode(5, OUTPUT);
    pinMode(4, OUTPUT);
    digitalWrite(6, LOW);
    digitalWrite(4, LOW);
    motors[0].pin1 = 5;
    motors[0].flags = MM_FLAG_ENABLED;

    // Enable motor 1 (Stepper)
    pinMode(8, OUTPUT);
    pinMode(9, OUTPUT);
    pinMode(10, OUTPUT);
    digitalWrite(8, LOW);
    digitalWrite(10, LOW);
    motors[1].pin1 = 9;
    motors[1].flags = MM_FLAG_ENABLED;

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
                if (motors[motor_idx].curCmd.flags & NC_FLAG_ENABLED) {
                    Serial.println("ERR motor busy");
                    goto done_processing;
                }

                // Set note
                motors[motor_idx].curCmd.delay = atoi(args[1]) / RESOLUTION;
                motors[motor_idx].curCmd.delayPos = 0;
                //motors[motor_idx].curCmd.repeat = atoi(args[2]);
                //motors[motor_idx].curCmd.repeatPos = 0;
                motors[motor_idx].curCmd.flags = NC_FLAG_ENABLED;
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
                if ((motors[motor_idx].curCmd.flags & NC_FLAG_ENABLED) == 0) {
                    Serial.println("ERR motor not busy");
                    goto done_processing;
                }

                motors[motor_idx].curCmd.flags &= ~NC_FLAG_ENABLED;
                Serial.println("OK");
                goto done_processing;
                
            done_processing:
                processing_command = false;
                break;
        }
    }
}

