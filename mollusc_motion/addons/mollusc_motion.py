
bl_info = {
    "name": "mollusc motion",
    "author": "clockdiv",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "category": "Hardware",
    "location": "Graph Editor -> Sidebar -> mollusc motion",
    "description": "an organic and open source motion capture and motion control system",
    "warning" : "It may take some seconds to enable the add-on because it might need to install pyserial",
    "doc_url": "https://clockdiv.github.io/mollusc-motion/",
    "tracker_url": ""
}


from typing import Set
import bpy
from bpy.types import Context
from bpy.utils import previews
from bpy.props import IntProperty, FloatProperty
import os
import struct
import math
from importlib import reload
import serial
import serial.tools.list_ports
# import XInput
# from molluscmotion.mapping import map_range
from molluscmotion import hardware
import molluscmotion.animation_handler
from molluscmotion.animation_handler import AnimationCurveModeHandler
from molluscmotion.mapping import map_range

import molluscmotion.file_handler
from molluscmotion.file_handler import save_to_disk
import molluscmotion.hardware

# global variables
custom_icons = None
spaghettimonster_hw = hardware.Spaghettimonster(name = 'Spaghettimonster')
mollusccontroller_hw = hardware.MotorControllerBoard(name = 'MolluscController')
# stop_modal = False
# modal_running = False
                        
# Serial Port Handler
class SerialPortHandler(bpy.types.PropertyGroup):
    serial_port_enum = []

    @staticmethod
    def update_serial_ports():
        """rescans the serial ports for new devices"""
        print('updating serial port list...')
        SerialPortHandler.serial_port_enum = hardware.SerialWrapper.get_serial_port_enum()

    def get_serial_port_list(self, context):
        """returns the enum with the serial ports to the serial-port_list EnumProperty"""
        return self.serial_port_enum

    def serial_port_changed(self, context):
        """called when the user choosen another serial port from the dropdown"""
        selected_serial_port = self.serial_port_list
        print('serial port changed, please connect now to:', self.get_selected_serialname())
        print('by the way, the int value is:', self.my_int)
    
    def get_selected_serialname(self):
        try:
            serial_port_index = int(self.serial_port_list)
        except:
            return 'no serial port selected'
        serial_port = ''
        for sp in self.serial_port_enum:
            if int(sp[0]) == serial_port_index:
                serial_port = sp[1]
                continue
        return serial_port

    my_bool: bpy.props.BoolProperty(
        name="Enable or Disable",
        description="A bool property",
        default = False
        )

    my_int: bpy.props.IntProperty(
        name = "Int Value",
        description="A integer property",
        default = 23,
        min = 10,
        max = 100
        )

    serial_port_list : bpy.props.EnumProperty(
        name = 'Port',
        description = 'List of all detected Serial Port',
        items = get_serial_port_list, 
        update = serial_port_changed
        )


def update_callback(self, context):
    try:
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
    except:
        pass
    return None

#                   Properties for Connection List

class MolluscConnection(bpy.types.PropertyGroup):
    """a single item in the list with a group of properties"""

    def get_custom_properties_as_enumlist(self, context):
        custom_properties_list = []
        tiny_puppeteer_object = context.scene.mollusc_object
        for prop in tiny_puppeteer_object.keys(): # run through all custom props
            p = (prop, prop, '') # identifier, name, description (here, identifier = name)
            custom_properties_list.append(p)
        return custom_properties_list
    
    def live_toggled(self, context):
        if self.enable_live == False:
            self.enable_rec = False

    def record_toggled(self, context):
        if self.enable_rec == True:
            self.enable_live = True

    def change_name(self, context):
        self.name = self.linked_property

    spaghettimonster_id : bpy.props.EnumProperty(
        name = 'Spaghettimonster ID',
        description = 'ID of the Spaghettimonster',
        items=[
            ('0', '0', ''),
            ('1', '1', ''),
            ('2', '2', ''),
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', '')
        ]
    )
    sensor_index : bpy.props.EnumProperty(
        name = 'Sensor Index',
        description = 'Index of the Sensor',
        items=[
            ('0', '0', ''),
            ('1', '1', ''),
            ('2', '2', ''),
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', '')
        ]
    )
    sensor_value : bpy.props.FloatProperty(
        name = 'Sensor Value',
        description = 'Value of the sensor',
        default = 0,
        # update = update_callback
    )
    sensor_map_min : bpy.props.IntProperty(
        name = 'Map Min',
        description = 'Map 0.0 of the sensor to this value',
        default = 0
    )
    sensor_map_max : bpy.props.IntProperty(
        name = 'Map Max',
        description = 'Map 1.0 of the sensor to this value',
        default = 1024
    )
    enable_invert : bpy.props.BoolProperty(
        name = 'Invert Live Input',
        description = 'Invert the sensor value for this channel',
        default = False
    )
    enable_live : bpy.props.BoolProperty(
        name = 'Enable Live Input',
        description = 'Enable input from Spaghettimonster for this channel',
        default = False,
        update = live_toggled
    )
    enable_rec : bpy.props.BoolProperty(
        name = 'Record Live Input',
        description = 'Record input from Spaghettimonster to this channel',
        default = False,
        update = record_toggled
    )
    linked_property : bpy.props.EnumProperty(
           name = 'Linked Property',
           description = 'The linked Custom Property',
           items = get_custom_properties_as_enumlist,
           update = change_name
    )

class LIST_UL_MolluscConnections(bpy.types.UIList):
    """UI List for Mollusc Connections"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_object = context.scene.mollusc_object

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            # Spaghettimonster and Sensor ID (enums)
            group = layout.row(align=True)
            group.prop(item, 'spaghettimonster_id', text='')
            group.prop(item, 'sensor_index', text='')

            # Sensor Value, Mapping
            layout.label(text = str(item.sensor_value))
            group = layout.row(align=True)
            group.prop(item, 'sensor_map_min', text='')
            group.prop(item, 'sensor_map_max', text='')

            # Enable Invert, Realtime-Mode and Recording
            group = layout.row(align=True)
            group.prop(item, 'enable_invert', text='', emboss=True, icon='MOD_LENGTH')
            group.prop(item, 'enable_live', text='', emboss=True, icon='ARMATURE_DATA')
            group.prop(item, 'enable_rec', text='', emboss=True, icon='SHADING_SOLID')

            # Linked Property (enum) to record to / to read data from
            layout.prop(item, 'linked_property', text='')
            # Value of the linked property
            if item.linked_property != '':
                layout.label(text = str(custom_object[item.linked_property]))
            else:
                layout.label(text = '-')

            # Index of the Item in the output CSV-String (=index in the list)
            layout.label(text = '['+str(index)+']')


#                   Properties for Save-To-Disk Panel

class MolluscMotionSaveToDiskProps(bpy.types.PropertyGroup):
    """a single item in the list with a group of properties"""
    start_frame : bpy.props.IntProperty(
        name = 'Start',
        description = 'Frame where the animation starts',
        default = 0
    )
    end_frame : bpy.props.IntProperty(
        name = 'End',
        description = 'Frame where the animation ends',
        default = 250
    )
    filename: bpy.props.StringProperty(
        name = 'Filename',
        description='Filename to store animation data to',
        subtype='FILE_PATH')


#                   Operators for Hardware Connections

class HARDWARE_OT_refresh_serial(bpy.types.Operator):
    bl_idname = 'hardware.refresh_serial'
    bl_label = 'Refresh'

    @classmethod
    def poll(cls, context):
        return True
    def execute(self, context):
        SerialPortHandler.update_serial_ports()
        return {'FINISHED'}

class HARDWARE_OT_connect_spaghettimonster(bpy.types.Operator):
    """the button to connect to the spaghettimonster"""
    bl_idname = 'hardware.connect_spaghettimonster'
    bl_label = 'Connect'
    @classmethod
    def poll(cls, context):
        return len(SerialPortHandler.serial_port_enum) and not spaghettimonster_hw.serial_device.is_open
    def execute(self, context):
        spaghettimonster_hw.connectSerial(context.scene.serial_port_spaghettimonster.get_selected_serialname())
        spaghettimonster_hw.set_mollusc_motion_connection_list(context.scene.mollusc_connections_list)
        return {'FINISHED'}

class HARDWARE_OT_connect_mollusccontroller(bpy.types.Operator):
    """the button to connect to the mollusccontroller"""
    bl_idname = 'hardware.connect_mollusccontroller'
    bl_label = 'Connect'
    @classmethod
    def poll(cls, context):
        return len(SerialPortHandler.serial_port_enum) and not mollusccontroller_hw.serial_device.is_open
    def execute(self, context):
        mollusccontroller_hw.connectSerial(context.scene.serial_port_monsterdriver.get_selected_serialname())
        return {'FINISHED'}

class HARDWARE_OT_disconnect_spaghettimonster(bpy.types.Operator):
    """the button to disconnect to the spaghettimonster"""
    bl_idname = 'hardware.disconnect_spaghettimonster'
    bl_label = 'Disconnect'
    @classmethod
    def poll(cls, context):
        return spaghettimonster_hw.serial_device.is_open
    def execute(self, context):
        spaghettimonster_hw.disconnectSerial()
        spaghettimonster_hw.set_mollusc_motion_connection_list(None)
        return {'FINISHED'}

class HARDWARE_OT_disconnect_mollusccontroller(bpy.types.Operator):
    """the button to disconnect from the mollusccontroller"""
    bl_idname = 'hardware.disconnect_mollusccontroller'
    bl_label = 'Disconnect'
    @classmethod
    def poll(cls, context):
        return mollusccontroller_hw.serial_device.is_open
    def execute(self, context):
        mollusccontroller_hw.disconnectSerial()

        return {'FINISHED'}


#                   Modal Operators

'''
class CONTROL_OT_Modal_XInput(bpy.types.Operator):
    """Move an object with the mouse, example"""
    bl_idname = "control.xinput"
    bl_label = "Simple Modal Operator"

    first_mouse_x: IntProperty()
    first_value: FloatProperty()

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            context.object.location.x = self.first_value + delta * 0.01

        elif event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.location.x = self.first_value
            return {'CANCELLED'}

        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object:
            self.first_mouse_x = event.mouse_x
            self.first_value = context.object.location.x

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}

def menu_func(self, context):
    self.layout.operator(CONTROL_OT_Modal_XInput.bl_idname, text=CONTROL_OT_Modal_XInput.bl_label)

'''
'''

class CONTROL_OT_Modal_XInput(bpy.types.Operator):
    """Modal Timer Example"""
    bl_idname = "control.xinput"
    bl_label = "Simple Modal Operator"

    # first_mouse_x: IntProperty()
    # first_value: FloatProperty()

    _timer = None

    def modal(self, context, event):
        global stop_modal
        global modal_running

        if event.type == 'TIMER':
            print(self._timer)
        
        if stop_modal == True:
            modal_running = False
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            return{'FINISHED'}
        
        return{'PASS_THROUGH'}
    
    def execute(self, context):
        global stop_modal
        global modal_running
        if modal_running == False:
            stop_modal = False
            modal_running = True

            wm = context.window_manager
            self._timer = wm.event_timer_add(.1, window=context.window)
            wm.modal_handler_add(self)
            return{'RUNNING_MODAL'}
        
        return {'CANCELLED'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

    # def invoke(self, context, event):
    #     if context.object:
    #         self.first_mouse_x = event.mouse_x
    #         self.first_value = context.object.location.x

    #         context.window_manager.modal_handler_add(self)
    #         return {'RUNNING_MODAL'}
    #     else:
    #         self.report({'WARNING'}, "No active object, could not finish")
    #         return {'CANCELLED'}
'''

#                   Operators for Mollucs Connections List

class LIST_OT_MolluscAddConnection(bpy.types.Operator):
    """Add a new connection item to the list."""

    bl_idname = "mollusc_connections_list.add_connection"
    bl_label = "Add connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        # create a new empty object if none exists       
        molluscmotion_object = context.scene.mollusc_object
        if molluscmotion_object == None:
            print('creating mollusc motion object...')
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            molluscmotion_object = context.active_object
            molluscmotion_object.name = 'mollusc motion'
            context.scene.mollusc_object = molluscmotion_object
            

        # name and create the custom property from user input:
        new_custom_prop = context.scene.new_prop_name
        i = 1
        while new_custom_prop in molluscmotion_object.keys():
            new_custom_prop = context.scene.new_prop_name + str(i)
            i += 1
        molluscmotion_object[new_custom_prop] = 0.0

        # setup the new custom prop on the mollusc object (change min/max values)
        molluscmotion_object.id_properties_ensure() # make sure manager is updated
        properties_manager = molluscmotion_object.id_properties_ui(new_custom_prop)
        properties_manager.update(min=0.0, max=1.0)

        new_item = context.scene.mollusc_connections_list.add()
        print('new custom prop name: ', end='')
        print(new_custom_prop)
        #new_item.name = new_custom_prop # the name should change when another property is selected, so that's not a good idea. 
        new_item.linked_property = new_custom_prop
        print(dir(new_item))
        # todo: link the custom prop to new_item, this has to be done manually now
         
        return{'FINISHED'}

class LIST_OT_MolluscDeleteConnection(bpy.types.Operator):
    """Deletes the selected connection from the list."""

    bl_idname = "mollusc_connections_list.delete_selected_connection"
    bl_label = "Delete selected connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.mollusc_connections_list_index
        context.scene.mollusc_connections_list.remove(context.scene.mollusc_connections_list_index) # remove from list
        return{'FINISHED'}
    
class LIST_OT_MolluscMoveConnectionUp(bpy.types.Operator):
    """Moves the selected item up in the list."""

    bl_idname = "mollusc_connections_list.move_connection_up"
    bl_label = "Move Up"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.mollusc_connections_list_index
        if index > 0:
            context.scene.mollusc_connections_list.move(index, index-1)
            context.scene.mollusc_connections_list_index = index - 1
        return{'FINISHED'}

class LIST_OT_MolluscMoveConnectionDown(bpy.types.Operator):
    """Moves the selected item down in the list."""

    bl_idname = "mollusc_connections_list.move_connection_down"
    bl_label = "Move Down"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.mollusc_connections_list_index
        max_index = len(context.scene.mollusc_connections_list) - 1
        if index < max_index:
            context.scene.mollusc_connections_list.move(index, index+1)
            context.scene.mollusc_connections_list_index = index + 1
        return{'FINISHED'}

'''
class LIST_OT_MolluscMotionStepperChannels_Add(bpy.types.Operator):
    """Add a new connection item to the list."""

    bl_idname = "molluscmotion_stepper_channels.add"
    bl_label = "Add connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        tiny_puppeteer_object = context.scene.mollusc_object
        if tiny_puppeteer_object == None:
            print('creating mollusc motion object...')
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            tiny_puppeteer_object = context.active_object
            tiny_puppeteer_object.name = 'mollusc motion'
            context.scene.mollusc_object = tiny_puppeteer_object
            

        # name and create the custom property from user input:
        new_custom_prop = context.scene.molluscmotion_stepper_channel_name
        i = 1
        while new_custom_prop in tiny_puppeteer_object.keys():
            new_custom_prop = context.scene.molluscmotion_stepper_channel_name + str(i)
            i += 1
        tiny_puppeteer_object[new_custom_prop] = 0.0

        # setup the new custom prop on the mollusc object (change min/max values)
        tiny_puppeteer_object.id_properties_ensure() # make sure manager is updated
        properties_manager = tiny_puppeteer_object.id_properties_ui(new_custom_prop)
        properties_manager.update(min=0.0, max=1.0)

        new_item = context.scene.molluscmotion_stepper_channels.add()
        # todo: link the custom prop to new_item, this has to be done manually now
         
        return{'FINISHED'}

class LIST_OT_MolluscMotionStepperChannels_Delete(bpy.types.Operator):
    """Deletes the selected connection from the list."""

    bl_idname = "molluscmotion_stepper_channels.delete"
    bl_label = "Delete selected connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_stepper_channel_index
        context.scene.molluscmotion_stepper_channels.remove(context.scene.molluscmotion_stepper_channel_index) # remove from list
        return{'FINISHED'}
    
class LIST_OT_MolluscMotionStepperChannels_MoveUp(bpy.types.Operator):
    """Moves the selected item up in the list."""

    bl_idname = "molluscmotion_stepper_channels.move_up"
    bl_label = "Move Up"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_stepper_channel_index
        if index > 0:
            context.scene.molluscmotion_stepper_channel_index.move(index, index-1)
            context.scene.molluscmotion_stepper_channel_index = index - 1
        return{'FINISHED'}

class LIST_OT_MolluscMotionStepperChannels_MoveDown(bpy.types.Operator):
    """Moves the selected item down in the list."""

    bl_idname = "molluscmotion_stepper_channels.move_down"
    bl_label = "Move Down"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_stepper_channel_index
        max_index = len(context.scene.molluscmotion_stepper_channel_index) - 1
        if index < max_index:
            context.scene.molluscmotion_stepper_channel_index.move(index, index+1)
            context.scene.molluscmotion_stepper_channel_index = index + 1
        return{'FINISHED'}


class LIST_OT_MolluscMotionDynamixelChannels_Add(bpy.types.Operator):
    """Add a new connection item to the list."""

    bl_idname = "molluscmotion_dynamixel_channels.add"
    bl_label = "Add connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        
        tiny_puppeteer_object = context.scene.mollusc_object
        if tiny_puppeteer_object == None:
            print('creating mollusc motion object...')
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            tiny_puppeteer_object = context.active_object
            tiny_puppeteer_object.name = 'mollusc motion'
            context.scene.mollusc_object = tiny_puppeteer_object
            

        # name and create the custom property from user input:
        new_custom_prop = context.scene.molluscmotion_dynamixel_channel_name
        i = 1
        while new_custom_prop in tiny_puppeteer_object.keys():
            new_custom_prop = context.scene.molluscmotion_dynamixel_channel_name + str(i)
            i += 1
        tiny_puppeteer_object[new_custom_prop] = 0.0

        # setup the new custom prop on the mollusc object (change min/max values)
        tiny_puppeteer_object.id_properties_ensure() # make sure manager is updated
        properties_manager = tiny_puppeteer_object.id_properties_ui(new_custom_prop)
        properties_manager.update(min=0.0, max=1.0)

        new_item = context.scene.molluscmotion_dynamixel_channels.add()
        # todo: link the custom prop to new_item, this has to be done manually now
         
        return{'FINISHED'}

class LIST_OT_MolluscMotionDynamixelChannels_Delete(bpy.types.Operator):
    """Deletes the selected connection from the list."""

    bl_idname = "molluscmotion_dynamixel_channels.delete"
    bl_label = "Delete selected connection"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_dynamixel_channel_index
        context.scene.molluscmotion_dynamixel_channels.remove(context.scene.molluscmotion_dynamixel_channel_index) # remove from list
        return{'FINISHED'}
    
class LIST_OT_MolluscMotionDynamixelChannels_MoveUp(bpy.types.Operator):
    """Moves the selected item up in the list."""

    bl_idname = "molluscmotion_dynamixel_channels.move_up"
    bl_label = "Move Up"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_dynamixel_channel_index
        if index > 0:
            context.scene.molluscmotion_dynamixel_channel_index.move(index, index-1)
            context.scene.molluscmotion_dynamixel_channel_index = index - 1
        return{'FINISHED'}

class LIST_OT_MolluscMotionDynamixelChannels_MoveDown(bpy.types.Operator):
    """Moves the selected item down in the list."""

    bl_idname = "molluscmotion_dynamixel_channels.move_down"
    bl_label = "Move Down"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        index = context.scene.molluscmotion_dynamixel_channel_index
        max_index = len(context.scene.molluscmotion_dynamixel_channel_index) - 1
        if index < max_index:
            context.scene.molluscmotion_dynamixel_channel_index.move(index, index+1)
            context.scene.molluscmotion_dynamixel_channel_index = index + 1
        return{'FINISHED'}
'''
'''
LIST_OT_MolluscMotionDynamixelChannels_Add
LIST_OT_MolluscMotionDynamixelChannels_Delete
LIST_OT_MolluscMotionDynamixelChannels_MoveUp
LIST_OT_MolluscMotionDynamixelChannels_MoveDown
'''


#                   Operator for Save-To-File Panel

class FILE_OT_MolluscMotion_SaveToFile(bpy.types.Operator):
    """Iterates the timeline in the range of the given start- and end frame and 
    saves the data to a binary file"""

    bl_idname = 'molluscmotion_save_to_disk.save_file'
    bl_label = 'Save to File'

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        start_frame = context.scene.molluscmotion_save_to_disk_props.start_frame
        end_frame = context.scene.molluscmotion_save_to_disk_props.end_frame
        filename = context.scene.molluscmotion_save_to_disk_props.filename
        scene = context.scene
        save_to_disk(scene, start_frame, end_frame, filename)
        return {'FINISHED'}

#                   Operator for Load-From-File Panel

class FILE_OT_MolluscMotion_LoadFromFile(bpy.types.Operator):
    """Loads binary data from a file"""

    bl_idname = 'molluscmotion_save_to_disk.load_file'
    bl_label = 'Load from File'

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default='*.bin', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        print('load from file')
        print(self.filepath)
        scene = context.scene
        try:
            # Open and read the selected file
            with open(self.filepath, 'rb') as file:
                file_contents = file.read()
                self.report({'INFO'}, "File read successfully")

                # Parsing the binary data into a list with unsigned int
                byte_count = 2
                animation_data = []
                for i in range(0, len(file_contents), byte_count):
                    value = struct.unpack_from('<H', file_contents, i)[0]
                    animation_data.append(value)

                # create a new empty object
                print('creating mollusc motion object...')
                bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
                molluscmotion_object = context.active_object
                molluscmotion_object.name = 'mollusc motion'

                # add the custom properties from the 'connections list' to the new object
                print('number of elements in mollusc_connection_list:')
                print(len(scene.mollusc_connections_list))
                prop_names = []
                mapping_min_values = []
                mapping_max_values = []
                for mollusc_connection in scene.mollusc_connections_list:
                    prop_name = 'Unnamed'
                    if mollusc_connection.name != '':
                        prop_name = mollusc_connection.name
                    molluscmotion_object[prop_name] = 0.0
                    prop_names.append(prop_name)
                    mapping_min_values.append(mollusc_connection.sensor_map_min)
                    mapping_max_values.append(mollusc_connection.sensor_map_max)

                # insert the keyframes for each channel
                start_frame = context.scene.molluscmotion_save_to_disk_props.start_frame
                current_frame = start_frame
                tracks_count = len(prop_names)
                print('tracks count: ' + str(tracks_count))
                for keyframe_value, i in zip(animation_data, range(0, len(animation_data))):
                    # normalize the 16-bit value to a float between 0 and 1
                    # according to the min/max setting of each connection-entry
                    track_index = i % tracks_count
                    prop_name_ = prop_names[track_index]
                    min = mapping_min_values[track_index]
                    max = mapping_max_values[track_index]
                    
                    keyframe_value_mapped = map_range(keyframe_value, min, max, 0.0, 1.0)
                    # print(prop_name_, keyframe_value, keyframe_value_mapped)

                    molluscmotion_object[prop_name_] = keyframe_value_mapped
                    molluscmotion_object.keyframe_insert(data_path = '["' + prop_name_ + '"]', frame = math.floor(current_frame))

                    current_frame += 1 / tracks_count



                # use the new object
                context.scene.mollusc_object = molluscmotion_object
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {e}")
            return {'CANCELLED'}


    def invoke(self, context, event):
        # Open the file selector dialog
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



#                   Operators for Set-Change Panel (Debug/WIP)

class SERIAL_OT_MolluscMotion_SetState_Manual(bpy.types.Operator):
    """Sends a command via serial to set the state of the
    mollusc motion board"""

    bl_idname = 'molluscmotion_set_state.manual'
    bl_label = 'Manual'

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        mollusccontroller_hw.send('MANUAL')
        return {'FINISHED'}

class SERIAL_OT_MolluscMotion_SetState_Idle(bpy.types.Operator):
    """Sends a command via serial to set the state of the
    mollusc motion board"""

    bl_idname = 'molluscmotion_set_state.idle'
    bl_label = 'Idle'

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        mollusccontroller_hw.send('IDLE')
        return {'FINISHED'}

class SERIAL_OT_MolluscMotion_SetState_Running(bpy.types.Operator):
    """Sends a command via serial to set the state of the
    mollusc motion board"""

    bl_idname = 'molluscmotion_set_state.running'
    bl_label = 'Running'

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        mollusccontroller_hw.send('RUNNING')
        return {'FINISHED'}

class SERIAL_OT_MolluscMotion_SetState_HomingA(bpy.types.Operator):
    """Sends a command via serial to set the state of the
    mollusc motion board"""

    bl_idname = 'molluscmotion_set_state.homing_a'
    bl_label = 'Homing A'

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        mollusccontroller_hw.send('HOMINGA')
        return {'FINISHED'}


'''
class CONTROL_OT_MolluscMotion_Modal_XInput_Start(bpy.types.Operator):
    """Starts the modal operator"""

    bl_idname = 'molluscmotion_modal.start'
    bl_label = 'Start Modal'

    @classmethod
    def poll(cls, context):
        global modal_running
        return not modal_running
    
    def execute(self, context):
        # bpy.ops.control.xinput('INVOKE_DEFAULT')        
        bpy.ops.control.xinput('EXEC_DEFAULT')        
        return {'FINISHED'}

class CONTROL_OT_MolluscMotion_Modal_XInput_Stop(bpy.types.Operator):
    """Stops the modal operator"""

    bl_idname = 'molluscmotion_modal.stop'
    bl_label = 'Stop Modal'

    @classmethod
    def poll(cls, context):
        global modal_running
        return modal_running
    
    def execute(self, context):
        global stop_modal
        stop_modal = True

        return {'FINISHED'}
'''


#                   Panels

class HARDWARE_PT_molluscmotion_setup(bpy.types.Panel):
    """Main panel for the 'mollusc motion' add-on"""
    bl_idname = 'HARDWARE_PT_MOLLUSC_MOTION_SETUP'
    bl_label = 'Setup'
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'mollusc motion'
        
    def draw(self, context):
        col = self.layout.column()

        # Logo, Imprint:
        imprint_row = col.row(align=True).split(factor=0.15)
        lfd_icon_id = custom_icons['icon_lfd'].icon_id
        imprint_row.template_icon(icon_value = lfd_icon_id, scale = 3)
        imprint_col_r = imprint_row.column()
        imprint_col_r.label(text=str(bl_info['name']))
        imprint_col_r.label(text=str(bl_info['description']))

        # box = col.box()
        # legal_text = 'Developed at the \'Digital Lab\' as part of the School for Performing Arts \'Ernst Busch\' in Berlin/Germany. The \'Digital Lab\' was funded by \'Stiftung Innovation in der Hochschullehre\'.'
        # box.template_icon(icon_value = lfd_icon_id, scale = 2)
        # box_split = box.split(factor=0.33)
        # box_left_col = box_split.column()
        # box_left_col.label(text = 'Author:')
        # box_left_col.label(text = 'Version:')
        # box_right_col = box_split.column()
        # box_right_col.label(text = str(bl_info['author']))
        # box_right_col.label(text = str(bl_info['version']))

        row = col.row(align=True).split(factor=0.15)
        
        # Object (e.g. an 'Empty') for mollusc motion:
        row.label(text='Object:')
        row.prop(context.scene, 'mollusc_object', text='')

        # Hardware Connection:
        hardware_devices_row = col.row()

        input_device_col = hardware_devices_row.column()
        input_device_col.label(text='Input Device:')
        input_device_row = input_device_col.row(align=True)
        input_device_row.prop(context.scene.serial_port_spaghettimonster, 'serial_port_list', text='')
        input_device_row.operator(HARDWARE_OT_refresh_serial.bl_idname, icon='FILE_REFRESH', text='')
        input_device_row = input_device_col.row(align=True)
        input_device_row.operator(HARDWARE_OT_connect_spaghettimonster.bl_idname)

        input_device_row.operator(HARDWARE_OT_disconnect_spaghettimonster.bl_idname)
        output_device_col = hardware_devices_row.column()
        output_device_col.label(text='Output Device:')
        output_device_row = output_device_col.row(align=True)
        output_device_row.prop(context.scene.serial_port_monsterdriver, 'serial_port_list', text='')
        output_device_row.operator(HARDWARE_OT_refresh_serial.bl_idname, icon='FILE_REFRESH', text='')
        output_device_row = output_device_col.row(align=True)
        output_device_row.operator(HARDWARE_OT_connect_mollusccontroller.bl_idname)
        output_device_row.operator(HARDWARE_OT_disconnect_mollusccontroller.bl_idname)

        col.separator()
        col.prop(context.scene, 'record_during_playback', text='Record during Playback (to the connections where \'rec\' is enabled)',
                  icon='SHADING_SOLID')
        col.prop(context.scene, 'enable_outputs')
        # col.label(text='Select Mode:')
        # op_mode_row=col.row()
        # op_mode_row.prop(context.scene.operation_mode, 'operation_mode', expand=True,text='')

class HARDWARE_PT_molluscmotion_connectionslist(bpy.types.Panel):
    """Main panel for the 'record data' add-on"""
    bl_idname = 'HARDWARE_PT_MOLLUSC_MOTION_CONNECTIONS_LIST'
    bl_label = 'Connections'
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'mollusc motion'
        
    def draw(self, context):
        col = self.layout.column()
        
        # List with custom properties:
        col.template_list("LIST_UL_MolluscConnections", "The_List", context.scene,
                          "mollusc_connections_list", context.scene, "mollusc_connections_list_index")
        row = col.row(align=False)
        row.prop(context.scene, 'new_prop_name', text='')
        row.operator(LIST_OT_MolluscAddConnection.bl_idname, text='', icon = 'ADD')
        row.operator(LIST_OT_MolluscDeleteConnection.bl_idname, text='', icon='REMOVE')
        row.operator(LIST_OT_MolluscMoveConnectionUp.bl_idname, text='', icon='TRIA_UP')
        row.operator(LIST_OT_MolluscMoveConnectionDown.bl_idname, text='', icon='TRIA_DOWN')
        col.separator_spacer()

        # # Stepper Motor Channels:
        # col.label(text='Stepper Motor Channels:')
        # col.template_list("LIST_UL_MolluscConnections", "Stepper Channels", context.scene,
        #                   "molluscmotion_stepper_channels", context.scene, "molluscmotion_stepper_channel_index")
        # row = col.row(align=True)
        # row.prop(context.scene, 'molluscmotion_stepper_channel_name', text='')
        # row.operator(LIST_OT_MolluscMotionStepperChannels_Add.bl_idname, text='', icon = 'ADD')
        # row.operator(LIST_OT_MolluscMotionStepperChannels_Delete.bl_idname, text='', icon='REMOVE')
        # row.operator(LIST_OT_MolluscMotionStepperChannels_MoveUp.bl_idname, text='', icon='TRIA_UP')
        # row.operator(LIST_OT_MolluscMotionStepperChannels_MoveDown.bl_idname, text='', icon='TRIA_DOWN')
        # col.separator_spacer()

        # # Dynamixel Channels:
        # col.label(text='Dynamixel Channels:')
        # col.template_list("LIST_UL_MolluscConnections", "Dynamixel Channels", context.scene,
        #                   "molluscmotion_dynamixel_channels", context.scene, "molluscmotion_dynamixel_channel_index")
        # row = col.row(align=True)
        # row.prop(context.scene, 'molluscmotion_dynamixel_channel_name', text='')
        # row.operator(LIST_OT_MolluscMotionDynamixelChannels_Add.bl_idname, text='', icon = 'ADD')
        # row.operator(LIST_OT_MolluscMotionDynamixelChannels_Delete.bl_idname, text='', icon='REMOVE')
        # row.operator(LIST_OT_MolluscMotionDynamixelChannels_MoveUp.bl_idname, text='', icon='TRIA_UP')
        # row.operator(LIST_OT_MolluscMotionDynamixelChannels_MoveDown.bl_idname, text='', icon='TRIA_DOWN')
        # col.separator_spacer()

        # # NeoPixel Channels:
        # col.label(text='NeoPixel Channels:')
        # col.template_list("LIST_UL_MolluscConnections", "Neopixel Channels", context.scene,
        #                   "molluscmotion_neopixel_channels", context.scene, "molluscmotion_neopixel_channel_index")
        
        # col.separator_spacer()
        

        # Move Up, Move Down, Delete, Add all, Delete all:
        # row_r = row.row(align=True)
        # row_r.operator(LIST_OT_AddAll.bl_idname)
        # row_r.operator(LIST_OT_DeleteAll.bl_idname)

        # Tiny Puppeteer Object:
        # col.label(text='Tiny Puppeteer Object:')
        # col.prop(context.scene.custom_properties_object, 'main_controller_object', text='')

        # Debug:
        # col.operator(LIST_OT_PrintInfo.bl_idname)

        # col.prop(context.scene.recording_object, 'recording_object', text='object to work with')
        # col.prop(context.scene.recorder, 'recording_object', text='object to work with')
        # col.operator(OBJECT_OT_add_custom_property.bl_idname)
        # col.prop(context.scene.recorder, 'is_recording', text='Record when playing')
        # col.prop(context.scene.recorder, 'float_value', text='Value')

class HARDWARE_PT_molluscmotion_save_and_load_file(bpy.types.Panel):
    """Panel to write and read the animation data to and from a binary file"""
    bl_idname = 'HARDWARE_PT_MOLLUSC_MOTION_SAVE_AND_LOAD_FILE'
    bl_label = 'Save and Load File'
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'mollusc motion'
        
    def draw(self, context):
        col = self.layout.column()
        
        start_end_col = col.column(align=True)
        start_end_col.use_property_split = True
        start_end_col.use_property_decorate = False  # No animation.
        start_end_col.prop(context.scene.molluscmotion_save_to_disk_props, 'start_frame', text='Frame Start')
        start_end_col.prop(context.scene.molluscmotion_save_to_disk_props, 'end_frame', text='End')
        
        filename_row = col.row()
        filename_row.use_property_split = True
        filename_row.use_property_decorate = False
        filename_row.prop(context.scene.molluscmotion_save_to_disk_props, 'filename')

        col.operator(FILE_OT_MolluscMotion_SaveToFile.bl_idname)

        col.operator(FILE_OT_MolluscMotion_LoadFromFile.bl_idname)

class HARDWARE_PT_molluscmotion_set_state(bpy.types.Panel):
    """Panel to set the state of the mollusc motion board"""  
    bl_idname = 'HARDWARE_PT_MOLLUSC_MOTION_SET_STATE'
    bl_label = 'Set State'
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'mollusc motion'

    def draw(self, context):
        row = self.layout.row()
        row.operator(SERIAL_OT_MolluscMotion_SetState_Manual.bl_idname)
        row.operator(SERIAL_OT_MolluscMotion_SetState_Idle.bl_idname)
        row.operator(SERIAL_OT_MolluscMotion_SetState_Running.bl_idname)
        row.operator(SERIAL_OT_MolluscMotion_SetState_HomingA.bl_idname)
        # row.operator(CONTROL_OT_MolluscMotion_Modal_XInput_Start.bl_idname)
        # row.operator(CONTROL_OT_MolluscMotion_Modal_XInput_Stop.bl_idname)


#                   Blender Registration

classes =  (HARDWARE_PT_molluscmotion_setup,
            HARDWARE_OT_refresh_serial,
            HARDWARE_OT_connect_spaghettimonster,
            HARDWARE_OT_connect_mollusccontroller,
            HARDWARE_OT_disconnect_spaghettimonster,
            HARDWARE_OT_disconnect_mollusccontroller,
            LIST_OT_MolluscAddConnection,
            LIST_OT_MolluscDeleteConnection,
            LIST_OT_MolluscMoveConnectionUp,
            LIST_OT_MolluscMoveConnectionDown,

            # LIST_OT_MolluscMotionStepperChannels_Add,
            # LIST_OT_MolluscMotionStepperChannels_Delete,
            # LIST_OT_MolluscMotionStepperChannels_MoveUp,
            # LIST_OT_MolluscMotionStepperChannels_MoveDown,

            # LIST_OT_MolluscMotionDynamixelChannels_Add,
            # LIST_OT_MolluscMotionDynamixelChannels_Delete,
            # LIST_OT_MolluscMotionDynamixelChannels_MoveUp,
            # LIST_OT_MolluscMotionDynamixelChannels_MoveDown,


            SerialPortHandler,
            # ControllerObject,
            # OperationMode,
            MolluscConnection,
            HARDWARE_PT_molluscmotion_connectionslist,
            LIST_UL_MolluscConnections,
            HARDWARE_PT_molluscmotion_save_and_load_file,
            MolluscMotionSaveToDiskProps,
            FILE_OT_MolluscMotion_SaveToFile,
            FILE_OT_MolluscMotion_LoadFromFile,
            SERIAL_OT_MolluscMotion_SetState_Manual,
            SERIAL_OT_MolluscMotion_SetState_Idle,
            SERIAL_OT_MolluscMotion_SetState_Running,
            SERIAL_OT_MolluscMotion_SetState_HomingA,
            HARDWARE_PT_molluscmotion_set_state,
            # CONTROL_OT_MolluscMotion_Modal_XInput_Start,
            # CONTROL_OT_MolluscMotion_Modal_XInput_Stop,
            # CONTROL_OT_Modal_XInput
            
            )

def register():
    reload(molluscmotion.file_handler) # for development only
    reload(molluscmotion.animation_handler)
    reload(molluscmotion.hardware)

    load_custom_icons()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.serial_port_spaghettimonster = bpy.props.PointerProperty(type=SerialPortHandler)
    bpy.types.Scene.serial_port_monsterdriver = bpy.props.PointerProperty(type=SerialPortHandler)
    bpy.types.Scene.mollusc_object = bpy.props.PointerProperty(name = 'Mollusc Object', type = bpy.types.Object)
    # bpy.types.Scene.operation_mode = bpy.props.PointerProperty(type=OperationMode)
    bpy.types.Scene.mollusc_connections_list = bpy.props.CollectionProperty(type = MolluscConnection) 
    bpy.types.Scene.mollusc_connections_list_index = bpy.props.IntProperty(name = '', default = 0)
    
    bpy.types.Scene.molluscmotion_stepper_channels = bpy.props.CollectionProperty(type = MolluscConnection) 
    bpy.types.Scene.molluscmotion_stepper_channel_index = bpy.props.IntProperty(name = '', default = 0)
    bpy.types.Scene.molluscmotion_stepper_channel_name = bpy.props.StringProperty(name = 'New Stepper Channel Name', default = 'Stepper')
    
    bpy.types.Scene.molluscmotion_dynamixel_channels = bpy.props.CollectionProperty(type = MolluscConnection) 
    bpy.types.Scene.molluscmotion_dynamixel_channel_index = bpy.props.IntProperty(name = '', default = 0)
    bpy.types.Scene.molluscmotion_dynamixel_channel_name = bpy.props.StringProperty(name = 'New Dynamixel Channel Name', default = 'Dynamixel')

    bpy.types.Scene.molluscmotion_neopixel_channels = bpy.props.CollectionProperty(type = MolluscConnection) 
    bpy.types.Scene.molluscmotion_neopixel_channel_index = bpy.props.IntProperty(name = '', default = 0)
    bpy.types.Scene.molluscmotion_neopixel_channel_name = bpy.props.StringProperty(name = 'New Neopixel Channel Name', default = 'NeoPixel')
    

    bpy.types.Scene.new_prop_name = bpy.props.StringProperty(name = 'New Properties Name', default = 'prop')
    bpy.types.Scene.enable_outputs = bpy.props.BoolProperty(name = 'Enable Outputs', default = False)
    bpy.types.Scene.record_during_playback = bpy.props.BoolProperty(name = 'Record During Playback', default = False)
    
    bpy.types.Scene.molluscmotion_save_to_disk_props = bpy.props.PointerProperty(type = MolluscMotionSaveToDiskProps) 

    bpy.app.handlers.frame_change_post.append(AnimationCurveModeHandler.frame_change_handler)
    bpy.app.handlers.depsgraph_update_post.append(AnimationCurveModeHandler.graph_editor_update_handler)
    bpy.app.handlers.animation_playback_pre.append(AnimationCurveModeHandler.animation_started_handler)
    bpy.app.handlers.animation_playback_post.append(AnimationCurveModeHandler.animation_ended_handler)

    SerialPortHandler.update_serial_ports()

    AnimationCurveModeHandler.set_mollusc_controller_hw(mollusccontroller_hw)
    AnimationCurveModeHandler.set_spaghettimonster_hw(spaghettimonster_hw)

    # bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    remove_custom_icons()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.serial_port_spaghettimonster
    del bpy.types.Scene.serial_port_monsterdriver
    del bpy.types.Scene.mollusc_object
    # del bpy.types.Scene.operation_mode
    del bpy.types.Scene.mollusc_connections_list
    del bpy.types.Scene.mollusc_connections_list_index
    del bpy.types.Scene.new_prop_name
    del bpy.types.Scene.record_during_playback
    del bpy.types.Scene.enable_outputs

    del bpy.types.Scene.molluscmotion_save_to_disk_props

    spaghettimonster_hw.disconnectSerial()
    mollusccontroller_hw.disconnectSerial()

    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.depsgraph_update_post.clear()
    bpy.app.handlers.animation_playback_pre.clear()
    bpy.app.handlers.animation_playback_post.clear()

    # bpy.types.VIEW3D_MT_object.remove(menu_func)

def load_custom_icons():
    global custom_icons
    addon_path = os.path.dirname(__file__)
    lfd_icon_file = os.path.join(addon_path, 'img/mm_logo.png')
    custom_icons = previews.new()
    custom_icons.load('icon_lfd', lfd_icon_file, 'IMAGE')
    
def remove_custom_icons():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

