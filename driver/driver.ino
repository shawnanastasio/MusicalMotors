#include <stdint.h>
#include <string.h>

#include <TimerOne.h>

/* PROGRAM CONSTANTS */
#define BAUD   115200  // Serial Baud rate to use
#define RESOLUTION 60  // Note resolution in microseconds. tick() is called at this interval
#define MAX_MOTORS 6   // Maximum number of motors supported

#define CMD_PLAY  0  // Serial command to play a note
#define CMD_STOP  1  // Serial command to stop playing a note
#define CMD_RESET 2  // Serial command to reset a motor (floppy only)
#define CMD_WIPE  3  // Serial command to wipe all installed motors
#define CMD_ADD   4  // Serial command to add a motor

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
#define MM_FLAG_NORESET (1<<4) // Should this drive not be reset?

struct NoteCommand {
    uint8_t delay;     // Current delay in ticks (microseconds / RESOLUTION)
    uint8_t delayPos;  // Current position in period
    uint8_t flags;
};

struct MusicalMotor {
    uint8_t stepPin; // Primary pin for steppers, STEP for floppies
    uint8_t dirPin;  // Unused for steppers, DIRECTION for floppies
    uint8_t flags;
    uint8_t floppyMax; // Maximum head position (only used on floppy)
    uint8_t floppyCur; // Current head position (only used on floppy)
    NoteCommand curCmd;
};

// List of motors
static uint8_t motorsLen = 0;
static volatile MusicalMotor motors[MAX_MOTORS];

/**
 * Interrupt handler called every `RESOLUTION` microseconds to handle motor steps
 */
#pragma GCC push_options
#pragma GCC optimize ("O3")
#pragma GCC optimize ("unroll-loops")

void tick() {
    // Go through all enabled motors and handle current note
    uint8_t i = MAX_MOTORS;
    while (i-- > 0) {
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
                        digitalWrite(motors[i].dirPin, motors[i].flags & MM_FLAG_HIGH2);
                        motors[i].floppyCur = 0;
                    }
                }
                
                // Toggle motor's pin's state
                motors[i].flags ^= MM_FLAG_HIGH1;
                digitalWrite(motors[i].stepPin, motors[i].flags & MM_FLAG_HIGH1);

                // Overflow, reset delayPos and increment repeatPos
                motors[i].curCmd.delayPos = 0;
            }
        }
    } 
}

#pragma GCC pop_options

void setup() {
    Serial.begin(BAUD);

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
                           // returns none

                // Get requested motor index
                motorIdx = serialReadBlocking();

                // Get noteDelay and set note command
                noteDelay = serialReadBlocking() << 8 | serialReadBlocking();
                motors[motorIdx].curCmd.delay = noteDelay / RESOLUTION;
                motors[motorIdx].curCmd.delayPos = 0;
                motors[motorIdx].curCmd.flags |= NC_FLAG_ENABLED;
                break;
            
            case CMD_STOP: // CMD_STOP usage: <motor idx>
                           // returns none

                // Get requested motor index
                motorIdx = serialReadBlocking();

                motors[motorIdx].curCmd.flags &= ~NC_FLAG_ENABLED;
                break;
            
            case CMD_RESET: // CMD_RESET usage: <motor idx>
                            // returns ERR_BADMOTOR, or ERR_SUCCESS

                // Get requested motor index
                motorIdx = serialReadBlocking();
                if (!(motors[motorIdx].flags & MM_FLAG_ENABLED)) {
                    Serial.write(ERR_BADMOTOR);
                    break;
                }

                // Steppers don't need to be reset
                if (!(motors[motorIdx].flags & MM_FLAG_FLOPPY)) {
                    Serial.write(ERR_SUCCESS);
                    break;
                }

                if (motors[motorIdx].flags & MM_FLAG_NORESET) {
                    Serial.write(ERR_SUCCESS);
                    break;
                }

                // Set the DIRECTION pin to HIGH (reverse) and run the head back to 0
                digitalWrite(motors[motorIdx].dirPin, HIGH);
                for (i=0; i<motors[motorIdx].floppyMax; i+=2) {
                    digitalWrite(motors[motorIdx].stepPin, HIGH);
                    digitalWrite(motors[motorIdx].stepPin, LOW);
                    delay(5);   
                }
                digitalWrite(motors[motorIdx].dirPin, LOW);
                motors[motorIdx].floppyCur = 0;
                motors[motorIdx].flags &= ~MM_FLAG_HIGH2;

                Serial.write(ERR_SUCCESS);
                break;

            case CMD_WIPE: // CMD_WIPE, returns ERR_SUCCESS
                motorsLen = 0; // Set length of motors array to 0
                Serial.write(ERR_SUCCESS);
                break;

            case CMD_ADD: // CMD_ADD: usage <step pin> <dir pin> <flags>
                          // returns: ERR_BADMOTOR or ERR_SUCCESS + motor_idx
                uint8_t step = serialReadBlocking();
                uint8_t dir = serialReadBlocking();
                uint8_t flags = serialReadBlocking();

                if (motorsLen >= MAX_MOTORS) {
                    Serial.write(ERR_BADMOTOR);
                    break;
                }

                pinMode(step, OUTPUT);
                pinMode(dir, OUTPUT);
                motorIdx = motorsLen++;
                motors[motorIdx].stepPin = step;
                motors[motorIdx].dirPin = dir;
                motors[motorIdx].flags = flags;
                motors[motorIdx].floppyCur = 0;
                motors[motorIdx].floppyMax = FLOPPY_DEFAULT_MAX;
                Serial.write(ERR_SUCCESS);
                Serial.write(motorIdx);
                break;
        }
    }
}
