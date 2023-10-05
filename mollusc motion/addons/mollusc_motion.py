
bl_info = {
    "name": "mollusc motion",
    "author": "Julian",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "category": "Hardware",
    "location": "",
    "description": "an organic and open source motion capture and motion control system",
    "warning" : "",
    "doc_url": "",
    "tracker_url": ""
}


import bpy
from bpy.utils import previews
import os
from molluscmotion import hardware
import serial
import serial.tools.list_ports
from molluscmotion.mapping import map_range
from molluscmotion.animation_handler import AnimationCurveModeHandler



# global variables
custom_icons = None
spaghettimonster_hw = hardware.Spaghettimonster(name = 'Spaghettimonster')
mollusccontroller_hw = hardware.MotorControllerBoard(name = 'MolluscController')
AnimationCurveModeHandler.set_mollusc_controller_hw(mollusccontroller_hw)
AnimationCurveModeHandler.set_spaghettimonster_hw(spaghettimonster_hw)

                        
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
        update = update_callback
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
           items = get_custom_properties_as_enumlist
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





#                   Operators for Mollucs Connections List

class LIST_OT_MolluscAddConnection(bpy.types.Operator):
    """Add a new connection item to the list."""

    bl_idname = "mollusc_connections_list.add_connection"
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
        new_custom_prop = context.scene.new_prop_name
        i = 1
        while new_custom_prop in tiny_puppeteer_object.keys():
            new_custom_prop = context.scene.new_prop_name + str(i)
            i += 1
        tiny_puppeteer_object[new_custom_prop] = 0.0

        # setup the new custom prop on the mollusc object (change min/max values)
        tiny_puppeteer_object.id_properties_ensure() # make sure manager is updated
        properties_manager = tiny_puppeteer_object.id_properties_ui(new_custom_prop)
        properties_manager.update(min=0.0, max=1.0)

        new_item = context.scene.mollusc_connections_list.add()
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

        # Add new Custom Property with specific name:
        row_l = row.row(align=True)
        row_l.prop(context.scene, 'new_prop_name', text='')
        row_l.operator(LIST_OT_MolluscAddConnection.bl_idname, text='', icon = 'ADD')
        row_l.operator(LIST_OT_MolluscDeleteConnection.bl_idname, text='', icon='REMOVE')
        row_l.operator(LIST_OT_MolluscMoveConnectionUp.bl_idname, text='', icon='TRIA_UP')
        row_l.operator(LIST_OT_MolluscMoveConnectionDown.bl_idname, text='', icon='TRIA_DOWN')

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
            SerialPortHandler,
            # ControllerObject,
            # OperationMode,
            MolluscConnection,
            HARDWARE_PT_molluscmotion_connectionslist,
            LIST_UL_MolluscConnections
            )

def register():
    load_custom_icons()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.serial_port_spaghettimonster = bpy.props.PointerProperty(type=SerialPortHandler)
    bpy.types.Scene.serial_port_monsterdriver = bpy.props.PointerProperty(type=SerialPortHandler)
    bpy.types.Scene.mollusc_object = bpy.props.PointerProperty(name = 'Mollusc Object', type = bpy.types.Object)
    # bpy.types.Scene.operation_mode = bpy.props.PointerProperty(type=OperationMode)
    bpy.types.Scene.mollusc_connections_list = bpy.props.CollectionProperty(type = MolluscConnection) 
    bpy.types.Scene.mollusc_connections_list_index = bpy.props.IntProperty(name = 'Spaghettimonster ID', default = 0)
    bpy.types.Scene.new_prop_name = bpy.props.StringProperty(name = 'New Properties Name', default = 'prop')
    bpy.types.Scene.record_during_playback = bpy.props.BoolProperty(name = 'Record During Playback', default = False)

    bpy.app.handlers.frame_change_post.append(AnimationCurveModeHandler.frame_change_handler)
    bpy.app.handlers.depsgraph_update_post.append(AnimationCurveModeHandler.graph_editor_update_handler)
    bpy.app.handlers.animation_playback_pre.append(AnimationCurveModeHandler.animation_started_handler)
    bpy.app.handlers.animation_playback_post.append(AnimationCurveModeHandler.animation_ended_handler)
    


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

    spaghettimonster_hw.disconnectSerial()
    mollusccontroller_hw.disconnectSerial()

    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.depsgraph_update_post.clear()
    bpy.app.handlers.animation_playback_pre.clear()
    bpy.app.handlers.animation_playback_post.clear()


def load_custom_icons():
    global custom_icons
    addon_path = os.path.dirname(__file__)
    lfd_icon_file = os.path.join(addon_path, 'img/mm_logo.png')
    custom_icons = previews.new()
    custom_icons.load('icon_lfd', lfd_icon_file, 'IMAGE')
    
def remove_custom_icons():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

