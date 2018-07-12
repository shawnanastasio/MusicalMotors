import os
import sys
import re
import traceback
import mido
from lxml import etree

from .musical_motor import *
from .serial_interface import *
from .scheduler import *

CUR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_SCHEMA_PATH = CUR_PATH + "/../schemas/config.xsd"
SONGCONFIG_SCHEMA_PATH = CUR_PATH + "/../schemas/songconfig.xsd"
DEFAULT_CONFIG_PATH = CUR_PATH + "/../config.xml"
XMLNS = "{https://anastas.io/MusicalMotors}"

class ConfigException(Exception):
    pass

def read_and_validate_xml(schema_path, file_path):
    schema_xml = etree.parse(schema_path)
    schema = etree.XMLSchema(schema_xml)
    parser = etree.XMLParser(schema=schema, attribute_defaults=True)
    file_xml = etree.parse(file_path, parser)
    return file_xml


class Config:
    """
    Class representing program configuration. Read from an XML file that adheres to
    the schema found in schemas/config.xsd.

    Public instance variables:
    serial: SerialInterface object connected to specified driver
    motors: List of MusicalMotor objects specified in config file
    """
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        try:
            # Read in the config at the default path and validate it
            xml = read_and_validate_xml(CONFIG_SCHEMA_PATH, config_path)
            root = xml.getroot()
           
            # We can now read in values without error checking since the
            # XML passed validation against the config schema

            # Read in serial port configuration
            sp = root.find(XMLNS + "serialPort")
            port = sp.text
            baud = int(sp.attrib["baud"])
            timeout = int(sp.attrib["timeout"])
            self.serial = SerialInterface(port, baud, timeout=timeout)

            # Read in motors
            self.motors = []
            motors = root.find(XMLNS + "motors")
            for m in motors:
                if "floppy" in m.tag:
                    # Add a new FloppyDrive to the motor list
                    step_pin = int(m.attrib["stepPin"])
                    dir_pin  = int(m.attrib["dirPin"])
                    transpose = True if "true" == m.attrib["transpose"] else False
                    octaves = [int(x) for x in re.split(",|, ", m.attrib["octaves"]) if len(x)]
                    self.motors.append(FloppyDrive(self.serial, step_pin, dir_pin, transpose=transpose, octaves=octaves))

                elif "stepper" in m.tag:
                    step_pin = int(m.attrib["stepPin"])
                    transpose = True if "true" == m.attrib["transpose"] else False
                    octaves = [int(x) for x in re.split(",|, ", m.attrib["octaves"]) if len(x)]
                    self.motors.append(StepperMotor(self.serial, step_pin, transpose=transpose, octaves=octaves)) 

        except SerialException as e:
            raise e

        except Exception as e:
            traceback.print_exc()
            raise ConfigException("Failed to parse configuration file: " + str(e) + 
                "\n\nSee config_example.xml for an example.\n")


class SongConfig:
    SCHEDULER_MAP = {
        "nop" : NopScheduler,
        "RoundRobin" : RoundRobinScheduler
    }

    """
    Class representing a song-specific configuration

    Public instance variables:
    map: list [idx=midi channel, val=[list of motors]]
    midi: mido midi object 
    scheduler: Scheduler object
    """
    def __init__(self, config, midi_path, remap=None, scheduler=None):
        """
        Parameters:
        config - Config object
        midi_path - String: path of midi
        remap = list of tuples (motor_idx, desired_channel)
        scheduler = Class (NOT object) of scheduler to use
        """
        self.config = config
        try:
            self.midi = mido.MidiFile(midi_path)
        except FileNotFoundError as e:
            raise ConfigException("Failed to open MIDI file: " + str(e))
       
        self.remap = remap
        
        self.generate_map()
        self.scheduler = scheduler(self.map) if scheduler is not None else NopScheduler(self.map)

    @classmethod
    def from_file(cls, config, path):
        try:
            xml = read_and_validate_xml(SONGCONFIG_SCHEMA_PATH, path)
            root = xml.getroot()

            # Read in midi path
            midi = root.find(XMLNS + "midi").text

            # Read in scheduler
            scheduler_name = root.find(XMLNS + "scheduler").text
            scheduler = SongConfig.SCHEDULER_MAP[scheduler_name]

            # Read in remap list if present
            remap = root.find(XMLNS + "remap")
            remap_list = None
            if remap is not None:
                remap_list = []
                for r in remap:
                    # Add this mapping to the remap list
                    remap_list.append((int(r.attrib["index"]), int(r.text)))
            
            # Call constructor with data   
            return cls(config, midi, remap=remap_list, scheduler=scheduler)

        except Exception as e:
            raise ConfigException("Failed to parse songconfig file: " + str(e) +
                    "\n\n See songconfig_example.xml for an example.\n")

    def generate_map(self):
        """
        Generate a motor map based off of the config's motor list and the remap list
        """
        self.map = [[] for _ in range(16)]

        # Handle motors with special remappings first
        handled_indexes = []
        if self.remap is not None:
            for r in self.remap:
                if r[0] > len(self.config.motors) or r[0] < 0:
                    raise ConfigException("Remap requested for invalid motor index {}!".format(r[0]))

                if r[0] in handled_indexes:
                    raise ConfigException("Double remap requested for motor index {}!".format(r[0]))

                self.map[r[1]].append(self.config.motors[r[0]])
                handled_indexes.append(r[0])
                
        # For motors with no remappings, just map their index to a midi channel 1:1
        for i in range(len(self.config.motors)):
            if i in handled_indexes:
                continue

            self.map[i % 16].append(self.config.motors[i])



