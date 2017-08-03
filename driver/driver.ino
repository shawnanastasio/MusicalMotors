#include <stdint.h>
#include <string.h>

#include <TimerOne.h>

/* PROGRAM CONSTANTS */
#define RESOLUTION 90  // Note resolution in microseconds. tick() is called at this interval
#define MAX_MOTORS 10  // Maximum number of motors supported
#define MAX_ARGS 5     // Maximum number of serial command arguments. Don't change this.

#define CMD_PLAY  'p'  // Serial command to play a note
#define CMD_STOP  's'  // Serial command to stop playing a note
#define CMD_RESET 'r'  // Serial command to reset a motor (floppy only)

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

/**
 * Interrupt handler called every `RESOLUTION` microseconds to handle motor steps
 */
#pragma GCC push_options
#pragma GCC optimize ("O3")
#pragma GCC optimize ("unroll-loops")

void tick() {
    // Go through all enabled motors and handle current note
    int i;
    for (i=0; i<MAX_MOTORS; i++) {
        if ((motors[i].flags & MM_FLAG_ENABLED) && (motors[i].curCmd.flags & NC_FLAG_ENABLED)) {
            // This motor is connected and has a note to play

            // Increment delayPos
            motors[i].curCmd.delayPos++;
            
            // Check for overflow and toggle pin state
            if (motors[i].curCmd.delayPos > motors[i].curCmd.delay) {
                
                // If this motor is a floppy drive handle DIRECTION swapping
                if (motors[i].flags & MM_FLAG_FLOPPY) {
                    motors[i].floppyCur++;
                    if (motors[i].floppyCur >= motors[i].floppyMax) {
                        motors[i].flags ^= MM_FLAG_HIGH2;
                        digitalWrite(motors[i].pin2, motors[i].flags & MM_FLAG_HIGH2);
                        motors[i].floppyCur = 0;
                    }
                }
                
                // Toggle motor's pin's state
                motors[i].flags ^= MM_FLAG_HIGH1;
                digitalWrite(motors[i].pin1, motors[i].flags & MM_FLAG_HIGH1);

                // Overflow, reset delayPos and increment repeatPos
                motors[i].curCmd.delayPos = 0;
            }
        }
    } 
}

#pragma GCC pop_options

void setup() {
    Serial.begin(115200);

#if 0 // Stepper Motor Installation
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
#endif
#if 0 // Floppy Drive Installation
    pinMode(2, OUTPUT);
    pinMode(3, OUTPUT);
    motors[0].pin1 = 2;
    motors[0].pin2 = 3;
    motors[0].flags = MM_FLAG_ENABLED | MM_FLAG_FLOPPY;
    motors[0].floppyMax = FLOPPY_DEFAULT_MAX;
    motors[0].floppyCur = 0;

    
    pinMode(4, OUTPUT);
    pinMode(5, OUTPUT);
    motors[1].pin1 = 4;
    motors[1].pin2 = 5;
    motors[1].flags = MM_FLAG_ENABLED | MM_FLAG_FLOPPY;
    motors[1].floppyMax = FLOPPY_DEFAULT_MAX;
    motors[1].floppyCur = 0;
#endif

    // Install timer
    Timer1.initialize(RESOLUTION);
    Timer1.attachInterrupt(tick);
}

volatile static bool processing_command = false;
static char *args[MAX_ARGS];
static int arg_len;
static char input_buf[256];

/**
 * Helper function to read arguments from serial and put in global args array
 */
__attribute__((always_inline)) static inline void getSerialArguments() {
    int i = Serial.readBytesUntil('\n', input_buf, 255);
    input_buf[i] = '\0';

    // Load arguments into `args` array
    char *tok = strtok(input_buf, " ");
    arg_len = 1;
    for (i=0; i<MAX_ARGS; i++) {
        args[i] = tok;
        tok = strtok(NULL, " ");
        if (tok) arg_len++;
        else break;
    }
}


void loop() {
    char *tok;
    int arg_len;
    int motor_idx;
    int i;
    if (Serial.available() && !processing_command) {
        processing_command = false;
        switch (Serial.read()) {
            case CMD_PLAY:
                // PLAY: usage: p <motor> <noteDelay>
                getSerialArguments();

                // If the requested motor already has a command, ignore
                motor_idx = atoi(args[0]);
                if (motors[motor_idx].curCmd.flags & NC_FLAG_ENABLED) {
                    Serial.println("ERR motor busy");
                    goto done_processing;
                }

                // Set note
                motors[motor_idx].curCmd.delay = atoi(args[1]) / RESOLUTION;
                motors[motor_idx].curCmd.delayPos = 0;
                motors[motor_idx].curCmd.flags |= NC_FLAG_ENABLED;
                Serial.println("OK");
                goto done_processing;

             case CMD_STOP:
                // STOP: usage: s <motor>
                getSerialArguments();

                motor_idx = atoi(args[0]);
                
                // Stop currently playing note
                if ((motors[motor_idx].curCmd.flags & NC_FLAG_ENABLED) == 0) {
                    Serial.println("ERR motor not busy");
                    goto done_processing;
                }

                motors[motor_idx].curCmd.flags &= ~NC_FLAG_ENABLED;
                Serial.println("OK");
                goto done_processing;
            
            case CMD_RESET:
                // RESET: usage: r <motor>
                // Floppy only!
                getSerialArguments();

                // Make sure the requested motor is a floppy and enabled
                motor_idx = atoi(args[0]);
                if ((motors[motor_idx].flags & MM_FLAG_FLOPPY) == 0) {
                    Serial.println("ERR motor not floppy");
                    goto done_processing;
                }

                // Set the DIRECTION pin to HIGH (reverse) and run the head back to 0
                digitalWrite(motors[motor_idx].pin2, HIGH);
                for (i=0; i<motors[motor_idx].floppyMax; i+=2) {
                    digitalWrite(motors[motor_idx].pin1, HIGH);
                    digitalWrite(motors[motor_idx].pin1, LOW);
                    delay(5);   
                }
                digitalWrite(motors[motor_idx].pin2, LOW);
                motors[motor_idx].floppyCur = 0;
                motors[motor_idx].flags &= ~MM_FLAG_HIGH2;

                Serial.println("OK");
                goto done_processing;
                
            done_processing:
                processing_command = false;
                break;
        }
    }
}

