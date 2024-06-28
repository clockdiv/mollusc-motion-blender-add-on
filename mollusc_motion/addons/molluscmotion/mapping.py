import bpy

def map_range(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


# Example usage

def clamp(x, out_min, out_max):
  if x > out_max:
    return out_max
  elif x < out_min:
    return out_min
  else:
    return x


'''
def map_animation_data(sm_data_floats):
    animation_data = [0] * 14
    servo_range = 512
    animation_data[0]  = int(sm_data_floats[2] * 56000)        # Stepper 1
    animation_data[1]  = int(sm_data_floats[3] * 41000)        # Stepper 2
    animation_data[2]  = int((1 - sm_data_floats[0]) * 53000)  # Stepper 3
    animation_data[3]  = int(2048 + ((servo_range / 2) - (sm_data_floats[1]  * servo_range))) # Servo 0
    animation_data[4]  = int(2048 + ((servo_range / 2) - (sm_data_floats[12] * servo_range))) # Servo 1
    animation_data[5]  = int(2048 + ((servo_range / 2) - (sm_data_floats[15] * servo_range))) # Servo 2
    animation_data[6]  = int(2048 + ((servo_range / 2) - (sm_data_floats[14] * servo_range))) # Servo 3
    animation_data[7]  = int(2048 + ((servo_range / 2) - (sm_data_floats[13] * servo_range))) # Servo 4
    animation_data[8]  = int(2048 + ((servo_range / 2) - (sm_data_floats[8]  * servo_range))) # Servo 5
    animation_data[9]  = int(2048 + ((servo_range / 2) - (sm_data_floats[16] * servo_range))) # Servo 6
    animation_data[10] = int(2048 + ((servo_range / 2) - (sm_data_floats[6]  * servo_range))) # Servo 7
    animation_data[11] = int(2048 + ((servo_range / 2) - (sm_data_floats[7]  * servo_range))) # Servo 8
    animation_data[12] = int(2048 + ((servo_range / 2) - (sm_data_floats[10] * servo_range))) # Servo 9
    animation_data[13] = int(2048 + ((servo_range / 2) - (sm_data_floats[9]  * servo_range))) # Servo 10
    # fill the servos temporarily with center position values:
    # for n in range(4,14):
    #     animation_data[n] = 2048
    return animation_data

def map_animation_data_2(sm_data_floats):
    animation_data = [0] * 14
    animation_data[0]  = int(sm_data_floats[2] * 56000)        # Stepper 1
    animation_data[1]  = int(sm_data_floats[3] * 41000)        # Stepper 2
    animation_data[2]  = int((1 - sm_data_floats[0]) * 53000)  # Stepper 3
    animation_data[3]  = int(map_range(sm_data_floats[1], 0, 1,  500, 4100)) # Servo 0
    animation_data[4]  = int(map_range(sm_data_floats[12],0, 1, 1250, 3070)) # Servo 1
    animation_data[5]  = int(map_range(sm_data_floats[15],0, 1, 1250, 2420)) # Servo 2
    animation_data[6]  = int(map_range(sm_data_floats[14],0, 1, 1730, 2310)) # Servo 3
    animation_data[7]  = int(map_range(sm_data_floats[13],0, 1, 1650, 2460)) # Servo 4
    animation_data[8]  = int(map_range(sm_data_floats[8] ,0, 1, 1024, 3070)) # Servo 5
    animation_data[9]  = int(map_range(sm_data_floats[16],0, 1, 1390, 2680)) # Servo 6
    animation_data[10] = int(map_range(sm_data_floats[6] ,0, 1, 1150, 3020)) # Servo 7
    animation_data[11] = int(map_range(sm_data_floats[7] ,0, 1, 1150, 2950)) # Servo 8
    animation_data[12] = int(map_range(sm_data_floats[10],0, 1, 1150, 2960)) # Servo 9
    animation_data[13] = int(map_range(sm_data_floats[9] ,0, 1, 1150, 2960)) # Servo 10
    # fill the servos temporarily with center position values:
    # for n in range(4,14):
    #     animation_data[n] = 2048
    return animation_data
'''