"""
This library consists of four classes and one function to assist with node
"""

from polyglot.nodeserver_api import Node
import sys
import time
import struct
from outback_defs import *
from pyModbusTCP.client import ModbusClient

# 1 for Normal/Info 2 for Debug
DEBUGLEVEL = '1'

class GSInverter(Node):
    """
    Instantiate a GSInverter Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['GS_Split_L1_Inverter_Output_Current', 'GS_Split_L1_Inverter_Charge_Current',
                                    'GS_Split_L1_Inverter_Buy_Current', 'GS_Split_L1_Inverter_Sell_Current',
                                    'GS_Split_L1_Grid_Input_AC_Voltage', 'GS_Split_L2_Inverter_Output_Current',
                                    'GS_Split_L2_Inverter_Charge_Current','GS_Split_L2_Inverter_Buy_Current',
                                    'GS_Split_L2_Inverter_Sell_Current', 'GS_Split_AC_Input_Selection',
                                    'GS_Split_AC_Input_State', 'GSconfig_Grid_AC_Input_Current_Limit', 
                                    'GSconfig_Gen_AC_Input_Current_Limit', 'GSconfig_Charger_AC_Input_Current_Limit', 
                                    'GSconfig_Charger_Operating_Mode', 'GSconfig_Sell_Volts'
                                    ]
    
    def __init__(self, parent, primary, address, device, name, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.primary = primary
        self.address = address
        self.device = device
        self.name = name
        self.registers = {}
        self.controller = self.parent.controller
        self.logger.info('Getting GS Inverter Registers')
        super(GSInverter, self).__init__(parent, address, self.name, primary, manifest)
        if not self.getRegisters(self.device):
            self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self, device):
        """
        getRegisters for the device based on the registers_needed
        
        :param device: The device to pull from
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] is not None:
                if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                self.set_driver(driver, self.registers[register])
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)
        return True

    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.controller.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)
        self.controller.closeConnection()
        return True

    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.parent.controller.openConnection()):  
            self.getRegisters(self.device)
        self.parent.controller.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'GV1': [0, 1, int], 'GV2': [0, 1, int],
                'GV3': [0, 1, int], 'GV4': [0, 1, int],
                'GV5': [0, 72, int], 'GV6': [0, 1, int],
                'GV7': [0, 1, int], 'GV8': [0, 1, float],
                'GV9': [0, 1, int], 'GV10': [0, 25, int],
                'GV11': [0, 25, int], 'GV12': [0, 1, float],
                'GV13': [0, 1, float], 'GV14': [0, 1, float],
                'GV15': [0, 25, int], 'GV16': [0, 72, float]
                }

    _commands = {'QUERY': query,
                            'GSconfig_Grid_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Gen_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Charger_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Charger_Operating_Mode': setRegister,
                            'GSconfig_Sell_Volts': setRegister
                            }
   
    node_def_id = 'gsinverter'

class GSSingleInverter(Node):
    """
    Instantiate a GS Single Phase Inverter Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['GS_Single_Inverter_Output_Current', 'GS_Single_Inverter_Charge_Current',
                                    'GS_Single_Inverter_Buy_Current', 'GS_Single_Inverter_Sell_Current',
                                    'GS_Single_Grid_Input_AC_Voltage', 'GS_Single_Inverter_Operating_mode',
                                    'GS_Single_AC_Input_Selection', 'GS_Single_AC_Input_State',
                                    'GSconfig_Grid_AC_Input_Current_Limit', 'GSconfig_Gen_AC_Input_Current_Limit',
                                    'GSconfig_Charger_AC_Input_Current_Limit', 'GSconfig_Charger_Operating_Mode',
                                    'GSconfig_Sell_Volts'
                                    ]
    
    def __init__(self, parent, primary, address, device, name, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.primary = primary
        self.address = address
        self.device = device
        self.name = name
        self.registers = {}
        self.controller = self.parent.controller
        self.logger.info('Getting GS Single Registers')
        super(GSSingleInverter, self).__init__(parent, address, self.name, primary, manifest)
        if not self.getRegisters(self.device):
            self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self, device):
        """
        getRegisters for the device based on the registers_needed
        
        :param device: The device to pull from
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] is not None:
                if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                self.set_driver(driver, self.registers[register])
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)
        return True

    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.controller.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)
        self.controller.closeConnection()
        return True

    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.parent.controller.openConnection()):  
            self.getRegisters(self.device)
        self.parent.controller.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'GV1': [0, 1, int], 'GV2': [0, 1, int],
                'GV3': [0, 1, int], 'GV4': [0, 1, int],
                'GV5': [0, 72, int], 'GV6': [0, 25, int],
                'GV7': [0, 25, int], 'GV8': [0, 25, int],
                'GV9': [0, 1, float], 'GV10': [0, 1, float],
                'GV11': [0, 1, float], 'GV12': [0, 25, int],
                'GV13': [0, 72, float]}

    _commands = {'QUERY': query,
                            'GSconfig_Grid_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Gen_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Charger_AC_Input_Current_Limit': setRegister,
                            'GSconfig_Charger_Operating_Mode': setRegister,
                            'GSconfig_Sell_Volts': setRegister
                            }
   
    node_def_id = 'gssinverter'

class SunSpecInverter(Node):
    """
    Instantiate a SunSpec Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['I_AC_Power', 'I_DC_Current',
                                    'I_DC_Voltage', 'I_DC_Power'
                                    ]
    
    def __init__(self, parent, primary, address, device, name, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.primary = primary
        self.address = address
        self.device = device
        self.name = name
        self.registers = {}
        self.controller = self.parent.controller
        self.logger.info('Getting SunSpec Inverter Registers')
        super(SunSpecInverter, self).__init__(parent, address, self.name, primary, manifest)
        if not self.getRegisters(self.device):
            self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self, device):
        """
        getRegisters for the device based on the registers_needed
        
        :param device: The device to pull from
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] is not None:
                if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                self.set_driver(driver, self.registers[register])
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)
        return True

    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.controller.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)
        self.controller.closeConnection()
        return True

    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.parent.controller.openConnection()):  
            self.getRegisters(self.device)
        self.parent.controller.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'GV1': [0, 73, float], 'GV2': [0, 1, float],
                'GV3': [0, 72, float], 'GV4': [0, 73, float]}

    _commands = {'QUERY': query}
   
    node_def_id = 'sunspec'

class FLEXNet(Node):
    """
    Instantiate a FLEXNet-DC Add-on Module Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['FN_Shunt_A_Current', 'FN_Shunt_B_Current',
                                    'FN_Shunt_C_Current', 'FN_Input_kW',
                                    'FN_Output_kW', 'FN_Net_kW',
                                    'FN_State_Of_Charge'
                                    ]
    
    def __init__(self, parent, primary, address, device, name, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.primary = primary
        self.address = address
        self.device = device
        self.name = name
        self.registers = {}
        self.controller = self.parent.controller
        self.logger.info('Getting FLEXnet-DC Registers')
        super(FLEXNet, self).__init__(parent, address, self.name, primary, manifest)
        if not self.getRegisters(self.device):
            self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self, device):
        """
        getRegisters for the device based on the registers_needed
        
        :param device: The device to pull from
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] is not None:
                if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                self.set_driver(driver, self.registers[register])
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)

        return True

    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.controller.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)
        self.controller.closeConnection()
        return True

    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.parent.controller.openConnection()):  
            self.getRegisters(self.device)
        self.parent.controller.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'GV1': [0, 1, float], 'GV2': [0, 1, float],
                'GV3': [0, 1, float], 'GV4': [0, 30, float],
                'GV3': [0, 30, float], 'GV4': [0, 30, float],
                'GV3': [0, 51, int]}

    _commands = {'QUERY': query}
   
    node_def_id = 'flexnet'

class FXInverter(Node):
    """
    Instantiate a FX Model Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['FX_Inverter_Output_Current', 'FX_Inverter_Charge_Current',
                                    'FX_Inverter_Buy_Current', 'FX_Inverter_Sell_Current',
                                    'FX_AC_Output_Voltage', 'FX_AC_Input_State',
                                    'FXconfig_AC_Input_Type', 'FXconfig_Grid_AC_Input_Current_Limit',
                                    'FXconfig_Gen_AC_Input_Current_Limit', 'FXconfig_Charger_AC_Input_Current_Limit',
                                    'FXconfig_Charger_Operating_Mode', 'FXconfig_Sell_Volts'
                                    ]
    
    def __init__(self, parent, primary, address, device, name, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.primary = primary
        self.address = address
        self.device = device
        self.name = name
        self.registers = {}
        self.controller = self.parent.controller
        self.logger.info('Getting FX Registers')
        super(FXInverter, self).__init__(parent, address, self.name, primary, manifest)
        if not self.getRegisters(self.device):
            self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self, device):
        """
        getRegisters for the device based on the registers_needed
        
        :param device: The device to pull from
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] is not None:
                if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                self.set_driver(driver, self.registers[register])
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)
        return True

    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.controller.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)
        self.controller.closeConnection()
        return True

    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.parent.controller.openConnection()):  
            self.getRegisters(self.device)
        self.parent.controller.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'GV1': [0, 1, int], 'GV2': [0, 1, int],
                'GV3': [0, 1, int], 'GV4': [0, 1, int],
                'GV5': [0, 72, int], 'GV6': [0, 25, int],
                'GV7': [0, 25, int], 'GV8': [0, 1, float],
                'GV9': [0, 1, float], 'GV10': [0, 1, float],
                'GV11': [0, 25, int], 'GV12': [0, 72, float]}

    _commands = {'QUERY': query,
                            'FXconfig_AC_Input_Type': setRegister,
                            'FXconfig_Grid_AC_Input_Current_Limit': setRegister,
                            'FXconfig_Gen_AC_Input_Current_Limit': setRegister,
                            'FXconfig_Charger_AC_Input_Current_Limit': setRegister,
                            'FXconfig_Charger_Operating_Mode': setRegister,
                            'FXconfig_Sell_Volts': setRegister
                            }
   
    node_def_id = 'fxinverter'

class OutbackNode(Node):
    """
    Instantiate the Main OutBack Type Node.
    
    :param parent: Parent node device (OutbackNodeServer)
    :param primary: True/False if this is the primary node
    :param address: Address of the node for ISY
    :param device: The device value we discovered from the AXS Port
    :param manifest: Directory of config values
    
    .. autoattribute:: _drivers
    .. autoattribute:: _commands
    .. autoattribute:: node_def_id
    .. autoattribute:: registers_needed
    """
    registers_needed = ['OutBack_Load_Grid_Transfer_Threshold', 'OutBack_Temp_Batt',
                                    'OB_Set_Sell_Voltage', 'OB_Set_Radian_Inverter_Sell_Current_Limit',
                                    'OB_Set_Inverter_Charger_Current_Limit', 'OB_Set_Inverter_AC1_Current_Limit',
                                    'OB_Set_Inverter_AC2_Current_Limit'
                                    ]
    master = None
    slaves = []

    def __init__(self, parent, address, name, primary, manifest=None):
        self.parent = parent
        self.address = address
        self.serial = None
        self.registers = {}
        self.uom = {}
        # Define the local logger for ease of calling
        self.logger = self.parent.poly.logger
        if (self.openConnection()):        
            # Get a list of all the devices attached to the deployment
            self.getDevices()
            # Determine what kind of setup this is. FX/GS, What phase type? FLEXnet-DC?
            self.determineSetup()
            # Retrieves the AXS Port Serial number for unique device name in ISY.
            self.serial = self.getSerial()
            if self.serial:
                self.address = self.serial
            # If we didn't find a valid deployment type, return and do nothing after reporting error.
            if DEPLOYMENTTYPE == None:
                self.logger.error('Invalid Deployment Type, No FX or GS deployments found.')
                C.close()
                return
            else:
                # Set the name string of the ISY Main Node to 'Outback FX/GS Single/Split/Three Phase'
                self.name = 'OutBack ' + str(DEPLOYMENTTYPE) + ' ' + str(DEPLOYMENTPHASE) + ' Phase'
            # Create OutBack System Controller Node in ISY
            super(OutbackNode, self).__init__(parent, self.address, self.name, primary, manifest)
            if not self.getRegisters():
                self.logger.error('Failed to get registers for %s', self.name)

    def getRegisters(self):
        """
        getRegisters for the device based on the registers_needed
        
        """
        for i, register in enumerate(self.registers_needed):
            devtype = getRegisterDevType(register)
            for dev in DEVICES:
                if dev.type == devtype:
                        self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            try:
                if self.registers[register] is not None:
                    if self.registers[register] == 'Not Implemented': self.registers[register] = 0
                    self.set_driver(driver, myfloat(self.registers[register]))
            except KeyError as e:
                self.logger.error('KeyError in getRegisters: %s', e)
        if DEBUGLEVEL == '2':
            self.logger.debug('%s', self.registers)
        return True

    def getSerial(self):
        """
        Gets the Serial number of the AXS Port (Used for address creation)
        """
        for device in DEVICES:
            if device.type == 1:
                return str(getOne(self.logger, device, 'C_SerialNumber'))[:14].lower()

    def addInverters(self, controller):
        """
        Finds all the different types of inverters and adds them to the ISY as appropriate.
        
        :param controller: The full controller object (aka self)
        """
        address = '' 
        name = ''
        manifest = self.parent.config.get('manifest', {})
        if DEPLOYMENTTYPE in ['FX', 'GS']:
            for device in DEVICES:
                if device.type == 64114:
                    self.logger.info('Stacking Mode: %i port %i', device.mode, device.port)
                    address = (DEPLOYMENTTYPE + '_inv_' + str(device.mode) + '_' + str(device.port)).lower()
                    lnode = self.parent.get_node(address)
                    if not lnode:
                        if device.mode in [0,4,10,19]:
                            #self.logger.info('get_node: %s', self.parent.get_node[self.address])
                            name = DEPLOYMENTTYPE + ' Inverter - Master - Port ' + str(device.port)
                            self.parent.inverter_master = FXInverter(self.parent, controller, address, device, name, manifest)
                        else:
                            name = DEPLOYMENTTYPE + ' Inverter - Slave - Port ' + str(device.port)
                            self.parent.inverter_slaves.append(FXInverter(self.parent, controller, address, device, name, manifest))
                elif device.type == 64116:
                    self.logger.info('Stacking Mode: %i port %i', device.mode, device.port)
                    address = (DEPLOYMENTTYPE + '_inv_' + str(device.mode) + '_' + str(device.port)).lower()
                    lnode = self.parent.get_node(address)
                    if not lnode:
                        if device.mode in [0,4,10,19]:
                            #self.logger.info('get_node: %s', self.parent.get_node[self.address])
                            name = DEPLOYMENTTYPE + ' Inverter - Master - Port ' + str(device.port)
                            if DEPLOYMENTPHASE == 'Single':
                                self.parent.inverter_master = GSSingleInverter(self.parent, controller, address, device, name, manifest)
                            else:
                                self.parent.inverter_master = GSInverter(self.parent, controller, address, device, name, manifest)
                        else:
                            name = DEPLOYMENTTYPE + ' Inverter - Slave - Port ' + str(device.port)
                            if DEPLOYMENTPHASE == 'Single':
                                self.parent.inverter_slaves.append(GSSingleInverter(self.parent, controller, address, device, name, manifest))
                            else:
                                self.parent.inverter_slaves.append(GSInverter(self.parent, controller, address, device, name, manifest))
                elif device.type == 64119:
                    address = (DEPLOYMENTTYPE + '_flexnet_' + str(device.port)).lower()
                    lnode = self.parent.get_node(address)
                    name = 'FLEXnet-DC'
                    if not lnode:
                        self.parent.flexnet = FLEXNet(self.parent, controller, address, device, name, manifest)
                elif device.type in [101, 102, 103]:
                    address = ('sunspec_' + str(device.type))
                    name = str('SunSpec ' + DEPLOYMENTPHASE + ' Phase Inverter')
                    lnode = self.parent.get_node(address)
                    if not lnode:
                        self.parent.sunspec = SunSpecInverter(self.parent, controller, address, device, name, manifest)
                    
    def update_info(self):
        """
        Update all the registers (runs on long_poll)
        """
        time.sleep(1)
        if (self.openConnection()):  
            self.getRegisters()
        self.closeConnection()
        return

    def query(self, **kwargs):
        """
        Get updated values for the registers
        """
        self.logger.info('Query for all registers and report.')
        self.parent.long_poll()
        self.parent.report_drivers()
        # Wait a few seconds and do it again. The ISY has a bad habit of missing some updates
        time.sleep(10)
        self.parent.report_drivers()
        return True

    class SunSpecDevice:
        """
        SunSpec Device Class
        
        :param parent: Parent
        :param id: ID (0 default)
        :param name: Name of device from sunspec tables
        :param type: Type of device from sunspec tables
        :param addr: Register Address
        :param offset: Register offset
        """
        def __init__(self, parent, id=0, name='', type=0, addr=0, offset=0):
            self.id = id
            self.parent = parent
            self.logger = self.parent.logger
            self.name = name
            self.type = type
            self.addr = addr
            self.offset = offset
            self.mode = None
            self.port = None
            self.logger.info('Added Device[%i]: %s at register address: %s device type: %s with the offset value of %s', self.id, self.name, self.addr, self.type, self.offset)

    def getDevices(self):
        """
        Function to get all the devices that are present in the system. Performs a scan of all the registers.
        """
        global DEPLOYMENTDEVICES
        nb = 2
        addr = ADDR_START
        device, offset = 0, 0
        while True:
            addr += (offset + 2)
            register = C.read_holding_registers(addr, nb)
            if ENCRYPTED: 
                for i in range(len(register)):
                    register[i] = DECRYPT(ENCRYPTIONKEY, register[i])
            #except TypeError as e:
            #register = DECRYPT(ENCRYPTIONKEY, register)
            DEVICES.insert(device, self.SunSpecDevice(self, device, SUNSPEC_DEVICE_LOOKUP.get(register[0]), register[0], addr, register[1]))
            DEPLOYMENTDEVICES.append(register[0])
            if register[0] == 64113:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'FX_Port_Number')
            elif register[0] == 64114:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'FXconfig_Port_Number')
                DEVICES[device].mode = getOne(self.logger, DEVICES[device], 'FXconfig_Stacking_Mode')
            elif register[0] == 64115:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'GS_Split_Port_number')
            elif register[0] == 64116:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'GSconfig_Port_number')
                DEVICES[device].mode = getOne(self.logger, DEVICES[device], 'GSconfig_Stacking_Mode')
            elif register[0] == 64117:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'GS_Single_Port_number')
            elif register[0] == 64118:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'FN_Port_Number')
            elif register[0] == 64119:
                DEVICES[device].port = getOne(self.logger, DEVICES[device], 'FNconfig_Port_Number')
            offset = register[1]
            if ((DEVICES[device].type == 65535) or (DEVICES[device].type == 0)): break
            device += 1
        DEVICES[0].addr -= 2
        self.logger.info('OutBack: %i devices were added', (device+1))

    def determineSetup(self):
        """
        Takes all the devices found and determines what kind of implementation we have
        and sets the global type constants.
        """
        global DEPLOYMENTCONFIG
        global DEPLOYMENTPHASE
        global DEPLOYMENTTYPE
        if SUNSPEC_INVERTER_SINGLE_DID in DEPLOYMENTDEVICES: DEPLOYMENTPHASE = 'Single'
        elif SUNSPEC_INVERTER_SPLIT_DID in DEPLOYMENTDEVICES: DEPLOYMENTPHASE = 'Split'
        elif SUNSPEC_INVERTER_3PHASE_DID in DEPLOYMENTDEVICES: DEPLOYMENTPHASE = 'Three'
        if SUNSPEC_OUTBACK_FX_DID in DEPLOYMENTDEVICES:
            DEPLOYMENTCONFIG = SUNSPEC_OUTBACK_FX_CONFIG_DID
            DEPLOYMENTTYPE = 'FX'
        elif (SUNSPEC_OUTBACK_GS_SPLIT_DID in DEVICES) or (SUNSPEC_OUTBACK_GS_SINGLE_DID in DEVICES):
            DEPLOYMENTCONFIG = SUNSPEC_OUTBACK_GS_CONFIG_DID
            DEPLOYMENTTYPE = 'GS'
        else:
            self.logger.error('Neither GS nor FX deployments found... thats fun.')
        self.logger.info(str(DEPLOYMENTTYPE) + ' ' + str(DEPLOYMENTPHASE) + ' phase deployment found. Config register at : ' + str(DEPLOYMENTCONFIG))
        if SUNSPEC_OUTBACK_FNDC_DID in DEPLOYMENTDEVICES:
            global FNDC
            global FNDCCONFIG
            FNDC = True
            FNDCCONFIG = SUNSPEC_OUTBACK_FNDC_CONFIG_DID
            self.logger.info('FLEXnet-DC Device Found. Config register at : ' + str(FNDCCONFIG))

    def verifySunSpec(self):
        '''
        Verify that the device returns the ID of a SunSpec device
        0x53756E53 at the first 2 bits of register 40000
        '''
        try: 
            register = C.read_holding_registers(SUNSPEC_MODBUS_REGISTER_OFFSET - 1, 2)
            sunSpecId = '0x{0:08X}'.format(register[0] << 16 | register[1])
            if sunSpecId == SUNSPECID: return True
        except:
            self.logger.info('Trying Encrypted')
        # Try Encrypted
        if self.getEncryptionKey():
            register = C.read_holding_registers(40000, 3)        
            register[1] = DECRYPT(ENCRYPTIONKEY,register[1])
            sunSpecId = '0x{0:08X}'.format((register[0] << 16) | register[1])
            # For testing
            # self.logger.info('ID: %s', sunSpecId)
            if sunSpecId == SUNSPECID: 
                global ENCRYPTED
                ENCRYPTED = True
                return True
            self.logger.info('Invalid register for SunSpec device type. 40000 should return 32-bit hex value of 0x53756E53')
        return False

    def openConnection(self):
        """
        The openConnection method to open/re-open or verify connection to AXS Port is open.
        """
        global C
        C = ModbusClient()
        C.host(DEVICEIP)
        C.port(DEVICEPORT)
        C.timeout(10)
        if not C.is_open():
            if not C.open():
                self.logger.info('Connection unsuccessful. Check IP or port settings')
                return False
        # Verify this is a SunSpec device at all
        if (self.verifySunSpec()): return True
        return False
            
    def getEncryptionKey(self):
        global ENCRYPTIONKEY
        try:
            ENCRYPTIONKEY = C.read_holding_registers(40076, 1)[0]
            if DEBUGLEVEL == '2':
                self.logger.debug('Encryption Key Found: %i', ENCRYPTIONKEY)
            return True
        except TypeError as e:
            self.logger.error('Failed to get Encryption Key, connection failed')
            return False

    def closeConnection(self):
        """
        Closes the connection to the AXS Port
        """
        C.close()
        
    def setRegister(self, **kwargs):
        """
        setRegister for the device based on input from the ISY
        
        :param kwargs: The input command from the ISY (dictionary)
        """
        self.logger.info('kwargs: %s', kwargs)
        register = kwargs.get('cmd')
        regtype = getRegisterDevType(register)
        value = kwargs.get('value')
        val = int()
        uom = kwargs.get('uom')
        self.logger.info('setRegister: %s(%i) UOM: %s = %s', register, regtype, uom, value)
        if (self.openConnection()):  
            for dev in DEVICES:
                if dev.type == regtype:
                    if uom == 25: val = int(value)
                    elif uom == 30: val = int(value * 10)
                    elif uom in [1, 72]: val = float(value * 10)
                    else: val = value
                    self.logger.info('Attempting setOne')
                    if setOne(self.logger, dev, register, val):
                        try:
                            self.set_driver('GV' + str((self.registers_needed.index(register) + 1)), value)
                        except ValueError as e:
                            self.logger.info('No ST field for the register: %s', register)                      
        self.closeConnection()
        return True

    _drivers = {
                'GV1': [0, 30, float], 'GV2': [0, 4, int],
                'GV3': [0, 72, float], 'GV4': [0, 1, float],
                'GV5': [0, 1, float], 'GV6': [0, 1, float],
                'GV7': [0, 1, float]
                }

    _commands = {'QUERY': query,
                            'OutBack_Load_Grid_Transfer_Threshold': setRegister,
                            'OB_Inverter_AC_Drop_Use': setRegister,
                            'OB_Set_Inverter_Mode': setRegister,
                            'OB_Grid_Tie_Mode': setRegister,
                            'OB_Set_Inverter_Charger_Mode': setRegister,
                            'OB_Set_Sell_Voltage': setRegister,
                            'OB_Set_Radian_Inverter_Sell_Current_Limit': setRegister,
                            'OB_Set_Inverter_Charger_Current_Limit': setRegister,
                            'OB_Set_Inverter_AC1_Current_Limit': setRegister,
                            'OB_Set_Inverter_AC2_Current_Limit': setRegister
                            }
                            
    node_def_id = 'outbackaxs'
    
def convert32bit(register):
    """
    Convert bits to '0x00000000' 32-bit notation

    :param register: Bit to convert.
    """
    if type(register) is not list: return
    return '0x{0:08X}'.format(register[0] | register[1] << 16)

def convertIP(register):
    """
    Convert bits to ip address notation
    """
    value = ''
    for bit in register:
        a,b = struct.unpack('2B', struct.pack('>H', bit))
        if value == '':
            value += str(a) + '.' + str(b)
        else:
            value += '.' + str(a) + '.' + str(b)
    return value

def convertString(register):
    """
    Convert bits to string
    """
    if register is None:
        return
    value = ''
    for bit in register:
        if ENCRYPTED == True: bit = DECRYPT(ENCRYPTIONKEY,bit)
        a,b = struct.unpack('2B', struct.pack('>H', bit))
        value += chr(a) + chr(b)
    return value
    
def convertFloat(register):
    """
    Convert bits to single decimal float. I.E '23.2'
    """
    if ENCRYPTED == True: register[0] = DECRYPT(ENCRYPTIONKEY,register[0])
    value = float(register[0]) / 10
    return '{0:.1f}'.format(value)

def convertFloat2(register):
    """
    Convert bits to two decimal float. I.E '23.23'
    """
    if ENCRYPTED == True: register[0] = DECRYPT(ENCRYPTIONKEY,register[0])
    value = float(register[0]) / 10
    return '{0:.2f}'.format(value)
    
def shortHex(register):
    """
    Convert bits to '0x0000' 16-bit notation
    """
    if register is not None:
        if ENCRYPTED == True: register = DECRYPT(ENCRYPTIONKEY,register)
        return '0x{0:04X}'.format(register)

def shortno0Hex(register):
    """
    Convert bits to '0000' 16-bit notation no prefixed '0x'
    """
    if register is not None:
        if ENCRYPTED == True: register[0] = DECRYPT(ENCRYPTIONKEY,register[0])
        return '{0:04X}'.format(register[0])

def longHex(register):
    """
    Convert bits to '0x00000000' 32-bit notation
    """
    if register is not None:
        if ENCRYPTED == True: 
            register[0] = DECRYPT(ENCRYPTIONKEY,register[0])
            register[1] = DECRYPT(ENCRYPTIONKEY,register[1])
        return '0x{0:08X}'.format(register[0] | register[1] << 16)

def checkRegister(register, register_type, register_valType, register_name):
    """
    Checks the Register and Converts it to the proper format for output.
    
    :param register: The Register returned from the device in bits
    :param register_type: The type returned from the defs tables.
    :param register_valType: The value type returned from the defs tables.
    :param register_name: The name of the register returned from the defs tables.
    """
    value = ''
    if  register_type == 'string':
        value = convertString(register)
    elif register_type == 'int32':
        value = convert32bit(register)
        if value == '0xFFFFFFFF' or value == '0x00000000':
            value = 'Not Implemented'
    elif register_type == 'float':
        value = convertFloat(register)
    elif register_type == 'float2':
        value = convertFloat2(register)
    elif register_type == 'ipaddress':
        value = convertIP(register)
    elif register_type == 'hex4':
        value = shortHex(register)
        if value == '0xFFFF':
            value = 'Not Implemented'
    elif register_type == 'uhex4':
        value = shortHex(register)
        if value == '0xFFFF':
            value = '-1'
        elif value == '0xFFFE':
            value = '-2'
        elif value == '0xFFFD':
            value = '-3'
        elif value == '0xFFFC':
            value = '-4'
        elif value == '0xFFFB':
            value = '-5'
        elif value == '0xFFFA':
            value = '-6'
        elif value == '0xFFF9':
            value = '-7'
        elif value == '0xFFF8':
            value = '-8'
        elif value == '0x0000':
            value = '0'
    elif register_type == 'hex8':
        value = longHex(register)
        if value == '0xFFFFFFFF' or value == '0x00000000':
            value = 'Not Implemented'
    else:
        if register[0] == 65535 or register[0] == 32768:
            value = 'Not Implemented'
        else:
            if ENCRYPTED == True: register[0] = DECRYPT(ENCRYPTIONKEY,register[0])
            if register_valType == 'ENUMERATED_U':
                if register_name == 'I_Status':
                    value = STATUS_MAP[register[0]]
            if value == '':
                value = register[0]
    return value

def getRegisterDevType(register):
    """
    Gets the device type of the register
    
    :param register: The register we are trying to find the type of
    """
    type = None
    regprefix = register.split('_')[0]
    if regprefix == 'OutBack': type = 64110
    elif regprefix == 'CC': type = 64111
    elif regprefix == 'CCconfig': type = 64112
    elif regprefix == 'GS': 
        if register.split('_')[1] == 'Split': type = 64115
        else: type = 64117
    elif regprefix == 'GSconfig': type = 64116
    elif regprefix == 'FX': type = 64113
    elif regprefix == 'FXconfig': type = 64114
    elif regprefix == 'FN': type = 64118
    elif regprefix == 'FNconfig': type = 64119
    elif regprefix == 'OB': type = 64120
    elif regprefix == 'C': type = 1
    elif regprefix == 'I': 
        if DEPLOYMENTPHASE == 'Single': type = 101
        elif DEPLOYMENTPHASE == 'Split': type = 102
        else: type = 103
    return type
    
def setOne(logger, device, regname, value):
    """
    setOne Method sets the value of a single register in the OutBack via the AXS Port Modbus interface
    
    :param logger: Passes the logger into the function as we don't use a global logger
    :param device: The device we are writing to
    :param regname: The register name we are writing to
    :param value: The value we are writing to the register
    """
    try:
         for i in range(len(SUNSPEC_DEVICE_MAP[device.type])):
            if SUNSPEC_DEVICE_MAP[device.type][i][7] == regname:
                address = device.addr + SUNSPEC_DEVICE_MAP[device.type][i][0] - 1
                if C.write_single_register(address, value):
                    logger.info('Wrote to register: ' + str(address) + ' Value: ' + str(value))
                else:
                    logger.error('Failed to write to register: ' + str(address) + ' Value: ' + str(value))
                    return False
                #logger.info(register_name + '(' + str(address) + '): ' + str(register_type) + ' : ' + str(value))
                return True
    except TypeError as e:
        logger.error('setOne ERROR: %s', e)

def getOne(logger, device, regname):
    """
    getOne Method gets the value of a single register in the OutBack via the AXS Port Modbus interface
    returns the value in bits
    
    :param logger: Passes the logger into the function as we don't use a global logger
    :param device: The device we are reading from
    :param regname: The register name we are reading
    """
    try:
         for i in range(len(SUNSPEC_DEVICE_MAP[device.type])):
            if SUNSPEC_DEVICE_MAP[device.type][i][7] == regname:
                address = device.addr + SUNSPEC_DEVICE_MAP[device.type][i][0] - 1
                register = C.read_holding_registers(address, SUNSPEC_DEVICE_MAP[device.type][i][1])
                register_type = SUNSPEC_DEVICE_MAP[device.type][i][2]
                register_valType = SUNSPEC_DEVICE_MAP[device.type][i][3]
                register_name = SUNSPEC_DEVICE_MAP[device.type][i][7]
                value = checkRegister(register, register_type, register_valType, register_name)
                # TODO: comment out before release
                # logger.info(register_name + '(' + str(address) + '): ' + str(register_type) + ' : ' + str(value))
                return value
    except TypeError as e:
        logger.error('getOne ERROR: %s', e)

def getAll(logger, devtype, port):
    """
    getAll Method gets the values of a all the registers in the OutBack via the AXS Port Modbus interface
    and logs all the values to the logger. This is currently not used for any functional part of the program
    this will be used as a test scenario at some point.
    
    :param logger: Passes the logger into the function as we don't use a global logger
    :param devtype: The device type that we are wanting to read all the registers for
    :param port: The port we want to read from we can have multiples of the same devices,
                            they will be on different ports in the configuration
    """
    for device in DEVICES:
        if device.type == devtype:
            if device.port == port:
                i = 0
                for i in range(len(SUNSPEC_DEVICE_MAP[device.type])):
                    address = device.addr + SUNSPEC_DEVICE_MAP[device.type][i][0] - 1
                    register = C.read_holding_registers(address, SUNSPEC_DEVICE_MAP[device.type][i][1])
                    register_type = SUNSPEC_DEVICE_MAP[device.type][i][2]
                    register_valType = SUNSPEC_DEVICE_MAP[device.type][i][3]
                    register_name = SUNSPEC_DEVICE_MAP[device.type][i][7]
                    value = checkRegister(register, register_type, register_valType, register_name)
                    
                    logger.info(register_name + '(' + str(address) + '): ' + str(register_type) + ' : ' + str(value))

def myfloat(value, prec=2):
    """
    Round and return float
    
    :param value: Value to convert to float
    :param prec: Decimal places (default 2)
    """
    return round(float(value), prec)                    
