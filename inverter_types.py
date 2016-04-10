from polyglot.nodeserver_api import Node
import requests
import sys
# from login import USERNAME, PASSWORD
import sunspec
# Globally disable SSL warnings from requests package.
requests.packages.urllib3.disable_warnings()


def myfloat(value, prec=2):
    """ round and return float """
    return round(float(value), prec)

class ModbusController(Node):
    
    def __init__(self, *args, **kwargs):
        super(ModbusController, self).__init__(*args, **kwargs)
    
    def _discover(self, **kwargs):
        self.LOGGER.info('Controller _discover')            
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}
    
    node_def_id = 'mbcontroller'

class ModbusNode(Node):
    
    def __init__(self, parent, primary, address, temperature, structurename, location, manifest=None):
        self.parent = parent
        self.LOGGER = self.parent.poly.LOGGER
        super(ModbusNode, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()
        
    def update_info(self):
        self.LOGGER.info('ModbusNode update_info')
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