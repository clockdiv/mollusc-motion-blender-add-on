import bpy
import csv

from molluscmotion.mapping import map_range
from molluscmotion.mapping import clamp


# class FileHandler():

#     @staticmethod
def save_to_disk(scene, start_frame, end_frame, filename):
    print('saving to disk...')    
    with open(filename + '.bin', 'wb') as f, open(filename + '.csv', 'w') as f_csv, open(filename + '_float.csv', 'w') as f_csv_float:
        byte_count = 2
        for frame in range(start_frame,end_frame+1):
            # get the custom properties in the correct order from the 'Connections'-Panel
            prop_data_list_float = []
            prop_data_list_int = []
            for mollusc_connection in scene.mollusc_connections_list:
                prop = mollusc_connection.linked_property

                # get the property-data from the mollusc_object at the specific frame
                prop_data = scene.mollusc_object.animation_data.action.fcurves.find(data_path=f'["{prop}"]').evaluate(frame)
                prop_data_list_float.append(prop_data)
                prop_data_mapped = int(map_range(prop_data, 0.0, 1.0, mollusc_connection.sensor_map_min, mollusc_connection.sensor_map_max))
                prop_data_mapped = int(clamp(prop_data_mapped, mollusc_connection.sensor_map_min, mollusc_connection.sensor_map_max))
                prop_data_list_int.append(prop_data_mapped)
                
                # print(prop_data, end='\t')
                # print(prop_data_mapped)

                # if(prop == '(1 / Z) Hoch Runter'):
                #     print(prop, end='\t')
                #     print(prop_data_mapped)

            # for p in prop_data_list_int:
            #     print(p)

            # Write data to binary file
            for value in prop_data_list_int:
                b = value.to_bytes(length=byte_count, byteorder='little', signed=False)
                f.write(b)

            # Write int data to CSV-file as well
            write = csv.writer(f_csv)
            write.writerow(prop_data_list_int)

            # Write float data to CSV-file as well
            write = csv.writer(f_csv_float)
            write.writerow(prop_data_list_float)

            # prop_data_list.clear()

    return


