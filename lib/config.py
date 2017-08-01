import configparser

CONFIG_PATH = "config.ini"

class Config(object):
    def __init__(self):
        # Read in the config file and return a Config object
        self.c = configparser.ConfigParser()
        self.c.read(CONFIG_PATH)
        self.arduino_port = self.c.get("Arduino", "SerialPort")
        self.baud = self.c.get("Arduino", "Baudrate")
