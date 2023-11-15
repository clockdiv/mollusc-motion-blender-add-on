import bpy
from bpy.utils import previews
import os
from molluscmotion import hardware
from molluscmotion.mapping import map_range
import serial
import serial.tools.list_ports


class AnimationCurveModeHandler():
    last_frame_sent = 0
    mollusccontroller_hw = None
    spaghettimonster_hw = None

    @staticmethod
    def frame_was_already_sent():
        current_frame = bpy.data.scenes[0].frame_current
        if(AnimationCurveModeHandler.last_frame_sent == current_frame):
            return True
        else:
            AnimationCurveModeHandler.last_frame_sent = current_frame
            return False
 
    @staticmethod
    def set_mollusc_controller_hw(mollusc_controller_hw):
        AnimationCurveModeHandler.mollusccontroller_hw = mollusc_controller_hw

    @staticmethod
    def set_spaghettimonster_hw(spaghettimonster_hw):
        AnimationCurveModeHandler.spaghettimonster_hw = spaghettimonster_hw

    @staticmethod
    # def get_animation_data(mollusc_connections_list, mollusc_object, global_record_enabled):
    def get_animation_data(scene):
        if not scene.enable_outputs:
            return

        """Creates a list from the custom properties of the ControllerObject.
        The list is send to the motorcontrollerboard in this order in send_animation_data()"""
        # mollusc_connections_list = scene.mollusc_connections_list
        # mollusc_object = scene.mollusc_object
        animation_data = []

        try:
            for mollusc_connection in scene.mollusc_connections_list:
                # if Live-Input enabled, get data from .sensor_value, else from .linked_property
                if mollusc_connection.enable_live == True:
                    connection_data = mollusc_connection.sensor_value
                    # connection_data = AnimationCurveModeHandler.spaghettimonster_hw.get_sm_data(mollusc_connection.spaghettimonster_id, mollusc_connection.sensor_index)
                    # record to mollusc_object if enable_rec is check
                    if mollusc_connection.enable_rec == True and scene.record_during_playback == True:
                        custom_property = mollusc_connection.linked_property
                        # scene.mollusc_object[custom_property] = mollusc_connection.sensor_value
                        scene.mollusc_object[custom_property] = connection_data
                        scene.mollusc_object.keyframe_insert(data_path = '["'+custom_property+'"]')
                else:
                    connection_data = scene.mollusc_object[mollusc_connection.linked_property]

                connection_data_mapped = int(map_range(connection_data, 0.0, 1.0, mollusc_connection.sensor_map_min, mollusc_connection.sensor_map_max))
                animation_data.append(connection_data_mapped)

        except KeyError:
            print('could not read the custom property data I was looking for')
            return [0]
         
        return animation_data

    @staticmethod
    def send_animation_data(animation_data):
        """sends the list with animation data - as prepared in get_animation_data()
        to the motorcontrollerboard as ascii csv data"""
        animation_data_csv_string = ','.join([str(ad) for ad in animation_data])
        # spaghettimonster_hw.send(animation_data_csv_string)
        AnimationCurveModeHandler.mollusccontroller_hw.send(animation_data_csv_string)

    @staticmethod
    def frame_change_handler(scene):        
        if AnimationCurveModeHandler.frame_was_already_sent(): 
            return
        try:
            # animation_data = AnimationCurveModeHandler.get_animation_data(scene.mollusc_connections_list, 
            #                                                               scene.mollusc_object, 
            #                                                               scene.record_during_playback)
            animation_data = AnimationCurveModeHandler.get_animation_data(scene)
        except TypeError:
            # print('No Object in \'Tiny Puppeteer Object\'')
            pass
        else:
            AnimationCurveModeHandler.send_animation_data(animation_data)

    @staticmethod
    def graph_editor_update_handler(scene):
        areatype = None
        try: 
            areatype = bpy.context.area.type
        except:
            pass
        else:
            if areatype == 'GRAPH_EDITOR':
                # print('graph editor, frame: ', end='')
                # print(bpy.data.scenes['Scene'].frame_current)
                try:
                    # ad = AnimationCurveModeHandler.get_animation_data(scene.mollusc_connections_list, scene.mollusc_object)
                    ad = AnimationCurveModeHandler.get_animation_data(scene)
                except TypeError:
                    # print('No Object in \'Tiny Puppeteer Object\'')
                    pass
                else:
                    AnimationCurveModeHandler.send_animation_data(ad)

    @staticmethod
    def animation_started_handler(scene):
        AnimationCurveModeHandler.mollusccontroller_hw.send('RUNNING')
    
    @staticmethod
    def animation_ended_handler(scene):
        AnimationCurveModeHandler.mollusccontroller_hw.send('MANUAL')