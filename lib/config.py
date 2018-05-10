import os
import sys
import re
import traceback
from lxml import etree

from .musical_motor import *
from .serial_interface import *

CUR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_SCHEMA_PATH = CUR_PATH + "/../schemas/config.xsd"
CONFIG_PATH = CUR_PATH + "/../config.xml"

class ConfigException(Exception):
    pass

def read_and_validate_xml(schema_path, file_path):
    schema_xml = etree.parse(schema_path)
    schema = etree.XMLSchema(schema_xml)
    parser = etree.XMLParser(schema=schema, attribute_defaults=True)
    file_xml = etree.parse(file_path, parser)
    return file_xml


class Config(object):
    """
    Class representing program configuration. Read from an XML file that adheres to
    the schema found in schemas/config.xsd.

    Public instance variables:
    serial: SerialInterface object connected to specified driver
    motors: List of MusicalMotor objects specified in config file
    """
    def __init__(self):
        try:
            # Read in the config at the default path and validate it
            xml = read_and_validate_xml(CONFIG_SCHEMA_PATH, CONFIG_PATH)
            root = xml.getroot()
           
            # We can now read in values without error checking since the
            # XML passed validation against the config schema

            # Read in serial port configuration
            sp = root.find("{https://anastas.io/MusicalMotors}serialPort")
            port = sp.text
            baud = int(sp.attrib["baud"])
            timeout = int(sp.attrib["timeout"])
            self.serial = SerialInterface(port, baud, timeout=timeout)

            # Read in motors
            self.motors = []
            motors = root.find("{https://anastas.io/MusicalMotors}motors")
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
