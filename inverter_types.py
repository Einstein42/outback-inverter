from polyglot.nodeserver_api import Node
import requests
import sys
import time
# from login import USERNAME, PASSWORD
import sunspec.core.client as client
from sunspec.core.client import SunSpecClientError
from sunspec.core.modbus.client import ModbusClientError
from pyModbusTCP.client import ModbusClient
# Globally disable SSL warnings from requests package.
requests.packages.urllib3.disable_warnings()


def myfloat(value, prec=2):
    """ round and return float """
    return round(float(value), prec)

class ModbusController(Node):
    
    def __init__(self, *args, **kwargs):
        super(ModbusController, self).__init__(*args, **kwargs)
    
    def _discover(self, **kwargs):
        self.logger.info('Controller _discover start.')
        try:
            d = client.SunSpecClientDevice(client.TCP, 0, None, None, None, None, '75.83.36.12', 502, 10)
            self.logger.info('Models: %s', d.models)
            d.common.read()
            self.logger.info('AXS Port Serial Number: %s', d.common)
            time.sleep(.5)
            #d.inverter.read()
            #self.logger.info('Inverter: %s', d.inverter)
            time.sleep(1)
            #d.axsport.read()
            #self.logger.info('!!!!!!! %s', d.axsport)
            d.close()
        except (SunSpecClientError,ModbusClientError) as e:
            self.logger.error('ClientError: %s', e)

        c = ModbusClient(host="75.83.36.12", auto_open=True)
        c.debug(True)
        regs = c.read_holding_registers(5, 10)
        self.logger.info('regs: %s', regs)
        c.close()
            
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}
    
    node_def_id = 'mbcontroller'

class ModbusNode(Node):
    
    def __init__(self, parent, primary, address, temperature, structurename, location, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        super(ModbusNode, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()
        
    def update_info(self):
        self.logger.info('ModbusNode update_info')
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