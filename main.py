from argparse import ArgumentParser

from classes.domjudge import DOMjudge
from classes.pta import PTA_school

from utils.argument_parser import argument_parser
from utils.config_loader import config_loader
import subprocess

import urllib3

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    argument = argument_parser()
    config = config_loader(argument['config'])
    # PTA_school(config).export(config['xml'])
    DOMjudge(config).export(config['xml'])

if __name__ == '__main__':
    main()
