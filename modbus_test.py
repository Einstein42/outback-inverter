#!/usr/bin/python

import requests
import sys
import time
import struct
# Import all the SunSpec specific definitions for Outback devices
from sunspec_defs import *

from pyModbusTCP.client import ModbusClient

# Put your SunSpec Device ID here. AXS Port
DEVICEIP = '75.83.36.12'
DEVICEPORT = '502'

# Do not modify below this line.
# Dynamic list of devices, contains a list of class objects 
DEVICES=[]
# Global Connection manager.
C = None

class SunSpecDevice:
    def __init__(self, id=0, name='', type=0, addr=0, offset=0):
        self.id = id
        self.name = name
        self.type = type
        self.addr = addr
        self.offset = offset
        print('Added Device[%i]: %s at register address: %s device type: %s with the offset value of %s' % (self.id, self.name, self.addr, self.type, self.offset))
        
def verifySunSpec():
    '''
    Verify that the device returns the ID of a SunSpec device
    0x53756E53 at the first 2 bits of register 40000
    '''
    try: 
        register = C.read_holding_registers(SUNSPEC_MODBUS_REGISTER_OFFSET - 1, 2)
        sunSpecId = '0x{0:08X}'.format(register[0] << 16 | register[1])
        if sunSpecId == SUNSPECID: return True
    except:
        print('Invalid register for SunSpec device type. 40000 should return 32-bit hex value of 0x53756E53')
    return False

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

def getDevices():
    nb = 2
    addr = ADDR_START
    device, offset = 0, 0
    while True:
        addr += (offset + 2)
        register = C.read_holding_registers(addr, nb)
        DEVICES.insert(device, SunSpecDevice(device, SUNSPEC_DEVICE_LOOKUP.get(register[0]), register[0], addr, register[1]))
        offset = register[1]
        if ((DEVICES[device].type == 65535) or (DEVICES[device].type == 0)): break
        device += 1
    DEVICES[0].addr -= 2
    print('SunSpec: %i devices were added'% (device+1))
        
def getAllCommon():
    for device in DEVICES:
        print device.type
        if device.type == 64120:
            i = 0
            for i in range(len(SUNSPEC_DEVICE_MAP[device.type])):
                value = ''
                address = device.addr + SUNSPEC_DEVICE_MAP[device.type][i][0] - 1
                register = C.read_holding_registers(address, SUNSPEC_DEVICE_MAP[device.type][i][1])
                register_type = SUNSPEC_DEVICE_MAP[device.type][i][2]
                register_valType = SUNSPEC_DEVICE_MAP[device.type][i][3]
                register_name = SUNSPEC_DEVICE_MAP[device.type][i][7]
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
                    
                print(register_name + '(' + str(address) + '): ' + str(register_type) + ' : ' + str(value))

def openConnection():
    global C
    C = ModbusClient(host=DEVICEIP, port=DEVICEPORT, auto_open=True, auto_close=False)

def main():
    openConnection()
    if (verifySunSpec()):
        getDevices()
        getAllCommon()
    C.close()

        
if __name__ == "__main__":
    main()
