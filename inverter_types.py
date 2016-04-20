from polyglot.nodeserver_api import Node
import sys
import time
import struct
from outback_defs import *
from pyModbusTCP.client import ModbusClient

class ModbusController(Node):
    
    def __init__(self, *args, **kwargs):
        super(ModbusController, self).__init__(*args, **kwargs)
    
    def _discover(self, **kwargs):
        self.logger.info('Controller _discover start.')
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}
   
    node_def_id = 'mbcontroller'

class OutbackNode(Node):

    def __init__(self, parent, primary, address, temperature, structurename, location, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        super(OutbackNode, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()
        
    def update_info(self):
        self.logger.info('OutbackNode update_info')
        return

    def _seton(self, **kwargs):
        self.update_info()
        return True

    def _setoff(self, **kwargs):
        self.update_info()
        return True

    def query(self, **kwargs):
        self.update_info()
        return True

    _drivers = {
                'GV1': [0, 14, int], 'GV2': [0, 14, int],
                'GV3': [0, 14, int], 'GV4': [0, 2, int],
                'ST': [0, 14, int]}

    _commands = {'DON': _seton,
                            'DOF': _setoff,
                            'QUERY': query}
                            
    node_def_id = 'mbnode'