#include <stdint.h>
#include <string.h>

#include <TimerOne.h>

/* PROGRAM CONSTANTS */
#define RESOLUTION 40  // Note resolution in microseconds. tick() is called at this interval
#define MAX_MOTORS 4   // Maximum number of motors supported

#define CMD_PLAY  0  // Serial command to play a note
#define CMD_STOP  1  // Serial command to stop playing a note
#define CMD_RESET 2  // Serial command to reset a motor (floppy only)

#define ERR_SUCCESS   0 // Serial return code for success
#define ERR_MOTORBUSY 1 // Serial return code for motor busy
#define ERR_BADMOTOR  2 // Serial return code for invalid motor

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
        if (motors[i].curCmd.flags & NC_FLAG_ENABLED) {
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
#if 1 // Floppy Drive Installation
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

    pinMode(6, OUTPUT);
    pinMode(7, OUTPUT);
    motors[2].pin1 = 6;
    motors[2].pin2 = 7;
    motors[2].flags = MM_FLAG_ENABLED | MM_FLAG_FLOPPY;
    motors[2].floppyMax = FLOPPY_DEFAULT_MAX;
    motors[2].floppyCur = 0;

    pinMode(8, OUTPUT);
    pinMode(9, OUTPUT);
    motors[3].pin1 = 8;
    motors[3].pin2 = 9;
    motors[3].flags = MM_FLAG_ENABLED | MM_FLAG_FLOPPY;
    motors[3].floppyMax = FLOPPY_DEFAULT_MAX;
    motors[3].floppyCur = 0;
#endif

    // Install timer
    Timer1.initialize(RESOLUTION);
    Timer1.attachInterrupt(tick);
}

static inline uint8_t serialReadBlocking() {
    while (Serial.available() == 0);
    return Serial.read();
}

void loop() {
    uint8_t motorIdx;
    uint16_t noteDelay;
    uint8_t i;

    if (Serial.available()) {
        switch (serialReadBlocking()) {
            case CMD_PLAY: // CMD_PLAY usage: <motor idx> <noteDelay[15:8]> <noteDelay[7:0]>

                // Get requested motor index
                motorIdx = serialReadBlocking();

                // Get noteDelay and set note command
                noteDelay = serialReadBlocking() << 8 | serialReadBlocking();
                motors[motorIdx].curCmd.delay = noteDelay / RESOLUTION;
                motors[motorIdx].curCmd.delayPos = 0;
                motors[motorIdx].curCmd.flags |= NC_FLAG_ENABLED;
                break;
            
            case CMD_STOP: // CMD_STOP usage: <motor idx>

                // Get requested motor index
                motorIdx = serialReadBlocking();

                motors[motorIdx].curCmd.flags &= ~NC_FLAG_ENABLED;
                break;
            
            case CMD_RESET: // CMD_RESET usage: <motor idx>

                // Get requested motor index
                motorIdx = serialReadBlocking();
                if (!(motors[motorIdx].flags & MM_FLAG_ENABLED)) {
                    Serial.write(ERR_BADMOTOR);
                    break;
                }

                // Set the DIRECTION pin to HIGH (reverse) and run the head back to 0
                digitalWrite(motors[motorIdx].pin2, HIGH);
                for (i=0; i<motors[motorIdx].floppyMax; i+=2) {
                    digitalWrite(motors[motorIdx].pin1, HIGH);
                    digitalWrite(motors[motorIdx].pin1, LOW);
                    delay(5);   
                }
                digitalWrite(motors[motorIdx].pin2, LOW);
                motors[motorIdx].floppyCur = 0;
                motors[motorIdx].flags &= ~MM_FLAG_HIGH2;

                Serial.write(ERR_SUCCESS);
                break;
        }
    }
}