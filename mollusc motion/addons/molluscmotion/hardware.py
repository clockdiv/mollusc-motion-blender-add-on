from threading import Thread
from time import sleep
# import time
import bpy
import math
from mathutils import Euler
import math
import subprocess
import sys
import json
from molluscmotion import mapping
from molluscmotion import animation_handler
# import animation_handler

try:
    import serial
except ModuleNotFoundError:
    print('Module pyserial not found, trying to install...')
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'pyserial'])
    import serial
    import serial.tools.list_ports
    print('pyserial installed and imported')


class SerialWrapper:
    def __init__(self, name):
        self.name = name
        self.serial_device = serial.Serial()
        self.run_thread = False

    @staticmethod
    def get_serial_port_enum():
        """rescans the serial ports for new devices"""
        """returns an enum with (index, name, description)"""
        serial_port_enum = []
        ports = serial.tools.list_ports.comports()
        for i, port in enumerate(ports):
            p = (str(i), port.name, '')
            serial_port_enum.append(p)
        return serial_port_enum

    def connectSerial(self, serialport):
        print('Connecting ' + self.name + ' to ' + serialport, end='...')
        self.serial_device.port = '/dev/' + serialport
        self.serial_device.baudrate = 500000
        self.serial_device.timeout = 0.1
        try:
            self.serial_device.open()
        except serial.SerialException:
            print('ERROR: Can\'t connect to ' + self.name)
        except:
            print('ERROR: Unknown Error when connnecting to ' + self.name)
        else:
            print('CONNECTED')
            # Start background thread to receive serial data
            thread = Thread(target = self.receiver_thread, args = (1, ))
            self.run_thread = True
            thread.start()
            # thread.join()

    def disconnectSerial(self):
        self.run_thread = False
        if self.serial_device.is_open:
            sleep(0.25)
            print('DISCONNECTED')
            self.serial_device.close()

    def parse_received_data(self, data):
        print('[[' + self.name + ']]', end = '')
        print('   ' + data.decode('utf-8'), end = '')

    def send(self, data):
        # print('attempting to send ' + data + ' to ' + self.name + '...', end='')
        if self.serial_device.is_open:
            # print('success.')
            data += '\n'
            self.serial_device.write(data.encode('utf-8'))
        else:
            # print('device not open.')
            pass
    
    def receiver_thread(self, args):
        print('Started thread for ' + self.name)
        while self.run_thread:
            received_bytes = self.serial_device.read_until(b'\n')
            if(received_bytes):
                # print(self.serial_device.name, end='')
                self.parse_received_data(received_bytes)
        print('Ended thread for ' + self.name)

class SpaghettimonsterDataError(Exception):
    'Unable to parse Data from Spaghettimonster'
    pass

class Spaghettimonster(SerialWrapper):
    monsterdriver_hw = None
    # sm_data_json = None
    mollusc_motion_connection_list = None

    def set_monsterdriver_hw(self, hw):
        print('set monsterdriver hardware')
        self.monsterdriver_hw = hw

    def set_mollusc_motion_connection_list(self, object):
        print('set mollusc motion list object')
        self.mollusc_motion_connection_list = object

    def spaghettimonster_to_armature(self, data):
        rotation_upper_arm = math.radians(data[3] * 360.0)
        bpy.data.objects['UpperArm'].rotation_euler = Euler((0, 0, rotation_upper_arm), 'XYZ')

        rotation_lower_arm = math.radians(data[0] * 360.0)
        bpy.data.objects['LowerArm'].rotation_euler = Euler((0, 0, rotation_lower_arm), 'XYZ')

    def spaghettimonster_to_monsterdriver(self, animation_data):
        if self.monsterdriver_hw:
            animation_data_csv_string = ','.join([str(ad) for ad in animation_data])
            # print(animation_data_csv_string)
            self.monsterdriver_hw.send(animation_data_csv_string)
        else:
            # print('No connection to controller board')
            pass

    # def get_sm_data(self, spaghettimonster_id, sensor_index):
    #     return self.sm_data_json[spaghettimonster_id][sensor_index]

    
    def decode_spaghettimonster(self, spaghettimonster_data):
        sm_data_json = json.loads(spaghettimonster_data)

        for key in sm_data_json:    # iterate through every spaghettimonster-id
            for mollusc_motion_connection in self.mollusc_motion_connection_list:  # find the spaghettimonster-id in the list of.. 
                if mollusc_motion_connection.spaghettimonster_id == key:           # ..connections from the mollusc motion list;
                    requested_index = int(mollusc_motion_connection.sensor_index)  # see which index the connection is looking for...
                    # print('spaghettimonster id:', end='')
                    # print(mollusc_motion_connection.spaghettimonster_id)
                    # print('data for that id:', end='')
                    # print(sm_data_json[key])
                    # print('requested_index:', end='')
                    # print(requested_index)
                    # print('value at requested index:', end='')
                    sensor = 0
                    try:
                        sensor = sm_data_json[key][requested_index]
                    except:
                        pass

                    if mollusc_motion_connection.enable_invert == True:
                        mollusc_motion_connection.sensor_value = 1.0 - sensor # ...and get the relevant sensor value from the array...
                    else:
                        mollusc_motion_connection.sensor_value = sensor # ...and get the relevant sensor value from the array...



        return
    
        # animation_data = [0] * 14

        if len(sm_data_json) == 18:  # that's the data length coming from 3 Spaghettimonsters (6 x 3)
            sm_data_floats = [float(i) for i in sm_data_json]

            animation_data = mapping.map_animation_data_2(sm_data_floats)

            # servo_range = 512    
            # sm_data_floats = [float(i) for i in sm_data]
            # animation_data[0]  = int(sm_data_floats[2] * 56000)        # Stepper 1
            # animation_data[1]  = int(sm_data_floats[3] * 41000)        # Stepper 2
            # animation_data[2]  = int((1 - sm_data_floats[0]) * 53000)  # Stepper 3
            # animation_data[3]  = int(2048 + ((servo_range / 2) - (sm_data_floats[1]  * servo_range))) # Servo 0
            # animation_data[4]  = int(2048 + ((servo_range / 2) - (sm_data_floats[12] * servo_range))) # Servo 1
            # animation_data[5]  = int(2048 + ((servo_range / 2) - (sm_data_floats[15] * servo_range))) # Servo 2
            # animation_data[6]  = int(2048 + ((servo_range / 2) - (sm_data_floats[14] * servo_range))) # Servo 3
            # animation_data[7]  = int(2048 + ((servo_range / 2) - (sm_data_floats[13] * servo_range))) # Servo 4
            # animation_data[8]  = int(2048 + ((servo_range / 2) - (sm_data_floats[8]  * servo_range))) # Servo 5
            # animation_data[9]  = int(2048 + ((servo_range / 2) - (sm_data_floats[16] * servo_range))) # Servo 6
            # animation_data[10] = int(2048 + ((servo_range / 2) - (sm_data_floats[6]  * servo_range))) # Servo 7
            # animation_data[11] = int(2048 + ((servo_range / 2) - (sm_data_floats[7]  * servo_range))) # Servo 8
            # animation_data[12] = int(2048 + ((servo_range / 2) - (sm_data_floats[10] * servo_range))) # Servo 9
            # animation_data[13] = int(2048 + ((servo_range / 2) - (sm_data_floats[9]  * servo_range))) # Servo 10

            # fill the servos temporarily with center position values:
            # for n in range(4,14):
            #     animation_data[n] = 2048

            self.spaghettimonster_to_monsterdriver(animation_data)
            # self.spaghettimonster_to_armature(sm_data_floats)
        else:
            raise SpaghettimonsterDataError


    def parse_received_data(self, data):
        try:
            spaghettimonster_data = data.decode('utf-8')
            self.decode_spaghettimonster(spaghettimonster_data)

            # If we are in live mode state, send the sensor data directly to the mollusc motion device.
            # The values from the sensors that are NOT in live mode are taken from the current frame of the timeline:
            # animation_data = animation_handler.AnimationCurveModeHandler.get_animation_data(bpy.context.scene)
            # animation_handler.AnimationCurveModeHandler.send_animation_data(animation_data)
            
        except SpaghettimonsterDataError:
            print('Spaghettimonster Data Error')
            print(data)
        except:
            print('[raw bytes] ', end='')
            print(data)

class MotorControllerBoard(SerialWrapper):
    pass