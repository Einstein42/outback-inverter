from polyglot.nodeserver_api import Node
import sys
import time
import struct
from outback_defs import *
from pyModbusTCP.client import ModbusClient

class FXInverter(Node):
    
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
        registers_needed = ['FX_Inverter_Output_Current', 'FX_Inverter_Charge_Current',
                                        'FX_Inverter_Buy_Current', 'FX_Inverter_Sell_Current',
                                        'FX_AC_Output_Voltage', 'FX_AC_Input_State',
                                        'FXconfig_AC_Input_Type', 'FXconfig_Grid_AC_Input_Current_Limit',
                                        'FXconfig_Gen_AC_Input_Current_Limit', 'FXconfig_Charger_AC_Input_Current_Limit',
                                        'FXconfig_Charger_Operating_Mode', 'FXconfig_Sell_Volts'
                                        ]

        for i, register in enumerate(registers_needed):
            if register.split('_')[0] == 'FX':
                for dev in DEVICES:
                    if dev.type == 64113:
                        if device.port == dev.port:
                            self.registers[register] = getOne(self.logger, dev, register)
            else:
                self.registers[register] = getOne(self.logger, device, register)
            driver = 'GV' + str(i+1)
            self.set_driver(driver, self.registers[register])

        self.logger.info('%s', self.registers)
        return True

    def query(self, **kwargs):
        if (self.controller.openConnection()):  
            self.getRegisters(self.device)
        self.controller.closeConnection()
        return True

    _drivers = {
                'GV1': [0, 1, int], 'GV2': [0, 1, int],
                'GV3': [0, 1, int], 'GV4': [0, 1, int],
                'GV5': [0, 72, int], 'GV6': [0, 25, int],
                'GV7': [0, 25, int], 'GV8': [0, 1, float],
                'GV9': [0, 1, float], 'GV10': [0, 1, float],
                'GV11': [0, 25, int], 'GV12': [0, 72, float]}

    _commands = {'QUERY': query}
   
    node_def_id = 'fxinverter'

class OutbackNode(Node):

    master = None
    slaves = []

    def __init__(self, parent, address, name, primary, manifest=None):
        self.parent = parent
        self.address = address
        self.serial = None
        self.registers = {}
        # Define the local logger for ease of calling
        self.logger = self.parent.poly.logger
        if (self.openConnection()):        
            # Verify this is a SunSpec device at all
            if (self.verifySunSpec()):
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
                    self.name = 'Outback ' + str(DEPLOYMENTTYPE) + ' ' + str(DEPLOYMENTPHASE) + ' Phase'
                # Create Outback System Controller Node in ISY
                super(OutbackNode, self).__init__(parent, self.address, self.name, primary, manifest)
                if not self.getRegisters():
                    self.logging.error('Failed to get registers for %s', self.name)

    def getRegisters(self):
        registers_needed = ['OutBack_Load_Grid_Transfer_Threshold', 'OutBack_Temp_Batt',
                                        'OB_Set_Sell_Voltage', 'OB_Set_Radian_Inverter_Sell_Current_Limit',
                                        'OB_Set_Inverter_Charger_Current_Limit', 'OB_Set_Inverter_AC1_Current_Limit',
                                        'OB_Set_Inverter_AC2_Current_Limit'
                                        ]
        for i, register in enumerate(registers_needed):
            if register.split('_')[0] == 'OutBack':
                for dev in DEVICES:
                    if dev.type == 64110:
                            self.registers[register] = getOne(self.logger, dev, register)
            elif register.split('_')[0] == 'OB':
                for dev in DEVICES:
                    if dev.type == 64120:
                        self.registers[register] = getOne(self.logger, dev, register)
            driver = 'GV' + str(i+1)
            if self.registers[register] == 'Not Implemented': self.registers[register] = 0
            self.set_driver(driver, self.registers[register])

        self.logger.info('%s', self.registers)
        return True

    def getSerial(self):
        for device in DEVICES:
            if device.type == 1:
                return str(getOne(self.logger, device, 'C_SerialNumber'))[:14].lower()

    def addInverters(self, controller):
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
                            self.parent.master_inverter = FXInverter(self.parent, controller, address, device, name, manifest)
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
                            self.parent.master_inverter = GSInverter(self.parent, controller, address, device, name, manifest)
                        else:
                            name = DEPLOYMENTTYPE + ' Inverter - Slave - Port ' + str(device.port)
                            self.parent.inverter_slaves.append(GSInverter(self.parent, controller, address, device, name, manifest))
                elif device.type == 64119:
                    address = (DEPLOYMENTTYPE + '_flexnet_' + str(device.port)).lower()
                    lnode = self.parent.get_node(address)
                    if not lnode:
                        self.parent.flexnet = FlexNet(self.parent, controller, address, device, name, manifest)
                    
    def update_info(self):
        self.logger.info('OutbackNode update_info')
        if (self.openConnection()):  
            self.getRegisters()
        self.closeConnection()
        return

    def query(self, **kwargs):
        self.update_info()
        return True

    class SunSpecDevice:
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
        global DEPLOYMENTDEVICES
        nb = 2
        addr = ADDR_START
        device, offset = 0, 0
        while True:
            addr += (offset + 2)
            register = C.read_holding_registers(addr, nb)
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
        self.logger.info('Outback: %i devices were added', (device+1))

    def determineSetup(self):
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
            self.logger.info('Invalid register for SunSpec device type. 40000 should return 32-bit hex value of 0x53756E53')
        return False

    def openConnection(self):
        global C
        C = ModbusClient()
        C.host(DEVICEIP)
        C.port(DEVICEPORT)
        C.timeout(10)
        if not C.is_open():
            if not C.open():
                self.logger.info('Connection unsuccessful. Check IP or port settings')
                return False
        return True

    def closeConnection(self):
        C.close()
        
    _drivers = {
                'GV1': [0, 30, float], 'GV2': [0, 4, int],
                'GV3': [0, 72, float], 'GV4': [0, 1, float],
                'GV5': [0, 1, float], 'GV6': [0, 1, float],
                'GV7': [0, 1, float]
                }

    _commands = {'QUERY': query}
                            
    node_def_id = 'outbackaxs'
    
def convert32bit(register):
    if type(register) is not list: return
    return '0x{0:08X}'.format(register[0] | register[1] << 16)

def convertIP(register):
    value = ''
    for bit in register:
        a,b = struct.unpack('2B', struct.pack('>H', bit))
        if value == '':
            value += str(a) + '.' + str(b)
        else:
            value += '.' + str(a) + '.' + str(b)
    return value

def convertString(register):
    if register is None:
        return
    value = ''
    for bit in register:
        a,b = struct.unpack('2B', struct.pack('>H', bit))
        value += chr(a) + chr(b)
    return value
    
def convertFloat(register):
    value = float(register[0]) / 10
    return '{0:.1f}'.format(value)

def convertFloat2(register):
    value = float(register[0]) / 10
    return '{0:.2f}'.format(value)
    
def shortHex(register):
    if register is not None:
        return '0x{0:04X}'.format(register[0])

def shortno0Hex(register):
    if register is not None:
        return '{0:04X}'.format(register[0])

def longHex(register):
    if register is not None:
        return '0x{0:08X}'.format(register[0] | register[1] << 16)

def checkRegister(register, register_type, register_valType, register_name):
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
            if register_valType == 'ENUMERATED_U':
                if register_name == 'I_Status':
                    value = STATUS_MAP[register[0]]
            if value == '':
                value = register[0]
    return value

def getOne(logger, device, regname):
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
                logger.info(register_name + '(' + str(address) + '): ' + str(register_type) + ' : ' + str(value))
                return value
    except TypeError as e:
        logger.error('ERROR: %s', e)
                  
def getAll(logger, devtype, port):
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