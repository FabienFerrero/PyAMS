import math
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from time import time
from RsInstrument.RsInstrument import RsInstrument
import serial
import Correlator_lib
# from pipython import GCSDevice, pitools
import mbx_functions as mbx


# Path to save the plots
path = "results/"

# Configure file name
num_meas = '230228'
AUT = 'Patch_27'

# Configure scan
angle_min = -20.0
angle_max = 20.0
angle_step = 0.5
# correlator_port_1_list = [1,2,3,4,5,6]  # Output ports of the correlator to measure on common port 1 of the correlator
correlator_port_1_list = [9, 5, 2, 3, 8, 12]  # Output ports of the correlator to measure on common port 1 of the correlator

vertical_angle_min = 87.0
vertical_angle_max = 93.0
vertical_angle_step = 3

# Configure VNA
freq_start=27.5  # in GHz
freq_stop=27.5   # in GHz
freq_points = 1
middle = freq_points-1
offset = -60


current_angle = angle_min
# Correlator related parameters
nb_common_ports = 4
nb_ports = 16
time_interval = 100  # in milliseconds

#  Connection to the correlator
print("Connecting correlator")
correlator = serial.Serial('COM6', 100000)
print("Correlator connected !")

#  Connection to the stepper motor controller
# gcs = GCSDevice('C-863.11')
# gcs_sn = "0021550330"
DEVICENAME = "COM9"
BAUDRATE = 1000000
MBX_VELOCITY_H = 3.0
MBX_VELOCITY_V = 3.0
FIX_H_ANGLE = 90

print("Connecting GCS")
# gcs.ConnectUSB(gcs_sn)
# print('GCS connected: {}'.format(gcs.qIDN().strip()))
mbx.connect(DEVICENAME, BAUDRATE)
axis = 1

print('=====================================')
print('============= Connection to the VNA')
print('=====================================')
instr = None
try:
    instr = RsInstrument('TCPIP::169.254.202.203::INSTR', True, True)  # Initializing the session
    instr.visa_timeout = 10000  # Timeout for VISA Read Operations
    instr.opc_timeout = 100000  # Timeout for opc-synchronised operations
    instr.instrument_status_checking = True  # Error check after each command
    instr.opc_query_after_write = True

except Exception as ex:
    print('Error initializing the instrument session:\n' + ex.args[0])
    exit()

print('\n VNA Connected !\n')

print(f'Driver Version: {instr.driver_version}')
print(f'SpecAn IDN: {instr.idn_string}')
print(f'visa_manufacturer: {instr.visa_manufacturer}')
print(f'full_instrument_model_name: {instr.full_instrument_model_name}')
print(f'instrument_serial_number: {instr.instrument_serial_number}')
print(f'firmware_version: {instr.instrument_firmware_version}')
print(f'instrument_options: List: {instr.instrument_options}')
print(f'opc_timeout: {instr.opc_timeout}')
print(f'visa_timeout: {instr.visa_timeout}')
print(f'SpecAn Options: {",".join(instr.instrument_options)}')

print('=====================================')
print('============= Configuration of the VNA')
print('=====================================')
instr.clear_status()  # Clean all subsystem instrument errors
instr.write_str('*RST')
instr.write_str(f'FREQ:STARt {freq_start} GHZ')
instr.write_str(f'FREQ:STOP  {freq_stop} GHZ')
#instr.write_str('FREQ:SPAN 100 MHz')
instr.write_str('BAND 100 Hz')  # RBW
instr.write_str('SOURce1:POWer 10dBm')  # RBW
instr.write_str('DISP:WIND:TRAC:Y:RLEV 0.0')  # Reference Level
instr.write_str('SYSTEM:DISPLAY:UPDATE ON')

print('\n VNA Configured !\n')

instr.write_str('INIT1')

#t = time()  # Start Time

instr.write_str('DISPLAY:WINDOW1:TRACE1:DELETE')
instr.write_str('SOURce1:PATH1:DIRectaccess B16')
instr.write_str('SOURce1:PATH2:DIRectaccess B16')
instr.write_str('DISP:WIND1:STAT ON')
instr.write_str(f'SWE:POIN {freq_points}')  # Sweep points

# ====== "Ch1Tr1" Configuration
instr.write_str('CALC1:PAR:SDEF "Ch1Tr1", "B2/A1D1"')  # Choose the ratio b2/a1 Port 1
instr.write_str('CALC1:FORM  MLOGarithmic; :DISP:WIND1:TRAC2:FEED "Ch1Tr1"')

# ===== "Ch1Tr2" Configuration
instr.write_str('CALC2:PAR:SDEF "Ch1Tr2","A2/A1D1"')  # Choose the ratio a2/a1 Port 1
instr.write_str('CALC2:FORM  MLOGarithmic; :DISP:WIND1:TRAC3:FEED "Ch1Tr2"')

#  Create a 1D array with the list of all the angle to take a measurement
angles_list = np.arange(angle_min, angle_max + 1, angle_step)
nb_points = len(angles_list)
print("Total number of points:", nb_points)

# Create 1D array of the sweep vertical angle
vertical_angles_list = np.arange(vertical_angle_min, vertical_angle_max + 1, vertical_angle_step)
vertical_nb_points = len(vertical_angles_list)

#  Customize the filename
info_measure = num_meas + AUT
filename = path + info_measure + '_' + str(angle_min) + '_' + str(angle_max) + '_' + str(angle_step)

# gcs.SVO(axis, 1)  # Set servo ON
# gcs.GOH()  # Go to the home position
# pitools.waitontarget(gcs, axis)
mbx.set_velocity(MBX_VELOCITY_H, MBX_VELOCITY_V)
mbx.gotoZERO();
mbx.gim_move(0, FIX_H_ANGLE, 0)
mbx.wait_stop_moving()
print("Homing complete !")
Correlator_lib.delay_ms(500)  # Wait a bit before the measurement begin

# gcs.MOV(axis, angle_min)  # Begin measurement at angle_min position
# pitools.waitontarget(gcs, axis)
# mbx.gim_move(angle_min, vertical_angle_min, 0)
mbx.wait_stop_moving()
mbx.set_velocity(0.25, 1)
print("Initial position Complete !")

#  Create 2 multidimensional arrays to store the measurements data
data_polar_1 = np.zeros((len(correlator_port_1_list), len(angles_list) * 2))
data_polar_2 = np.zeros((len(correlator_port_1_list), len(angles_list) * 2))

# plt.ion()
# plt.show()

# Create line with all 0-values
# fig = plt.figure()
# ax = fig.add_subplot(111)
plt.rcParams.update({'font.size': 8})
fig, ax = plt.subplots(vertical_nb_points)

# Properties initialization for subplots
line_array = []
for vertical_angle_idx in range(vertical_nb_points):
    ax[vertical_angle_idx].set_ylim(10, 30)
    ax[vertical_angle_idx].title.set_text('Elevation = ' + str(vertical_angles_list[vertical_angle_idx]) + ' deg')
    ax[vertical_angle_idx].set_xlabel('Phi (degree)')
    ax[vertical_angle_idx].set_ylabel('Mag (dB)')

    zeros_y_axis = np.zeros((len(angles_list), 1))
    line1, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 1', lw=1)
    line2, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 2', lw=1)
    line3, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 3', lw=1)
    line4, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 4', lw=1)
    line5, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 5', lw=1)
    line6, = ax[vertical_angle_idx].plot(angles_list, zeros_y_axis, label='Port 6', lw=1)
    line_array.append([line1, line2, line3, line4, line5, line6])
    ax[vertical_angle_idx].legend(loc='best', ncol=3)
    ax[vertical_angle_idx].grid()

# plt.title('Total Gain')
# plt.xlabel('Phi (degree)')
# plt.ylabel('Mag (dB)')
fig.tight_layout()
fig.canvas.set_window_title('Total Gain')
plt.ion()
plt.show()

for vertical_angle_idx in range(vertical_nb_points):

    # Calculation
    # Create multidimensional arrays to store the results of the calculations for each measured port
    amplitude_polar_1 = np.zeros((len(correlator_port_1_list), len(angles_list)))
    amplitude_polar_2 = np.zeros((len(correlator_port_1_list), len(angles_list)))
    total_gain = np.zeros((len(correlator_port_1_list), len(angles_list)))

    # mbx.gim_move(angle_min, vertical_angles_list[vertical_angle_idx], 0)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.draw()

    # Maximum the plotting window (These functions are stupid, don't use them)
    # mng = plt.get_current_fig_manager()
    # mng.full_screen_toggle()

    horizontal_index_array = range(len(angles_list))
    if (vertical_angle_idx % 2) == 1:
        horizontal_index_array = reversed(horizontal_index_array)

    for i in horizontal_index_array:

        # Preparing for next measurement
        print(f'Changing angle {i}/{len(angles_list)}, {(i / len(angles_list) * 100):.0f} %')
        print(f'Angle is {angles_list[i]}')
        # gcs.MVR(axis, angle_step)  # Move to the next angle
        # mbx.move(axis, angle_step)
        # mbx.wait_stop_moving()
        mbx.gim_move(angles_list[i], vertical_angles_list[vertical_angle_idx], 0)
        mbx.wait_stop_moving()
        current_angle = current_angle+angle_step
        # pitools.waitontarget(gcs, axis)

        Correlator_lib.delay_ms(100)  # Delay
        print("Measure...")

        for j in range(len(correlator_port_1_list)):
            # Selecting the port on the correlator
            Correlator_lib.change_port(correlator, 1, correlator_port_1_list[j])
            Correlator_lib.delay_ms(100)  # Delay

            # Trace 1
            instr.write_str(':CALCULATE1:PARAMETER:SELECT "Ch1Tr1"')
            temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH1DATA')
            data_polar_1[j][2 * i] = temp[middle]  # Re
            data_polar_1[j][2 * i + 1] = temp[middle+1]  # Im

            # Trace 2
            instr.write_str(':CALCULATE2:PARAMETER:SELECT "Ch1Tr2"')
            temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH2DATA')
            data_polar_2[j][2 * i] = temp[middle]  # Re
            data_polar_2[j][2 * i + 1] = temp[middle+1]  # Im

            # Calculate Re and Im
            temp1_Re = data_polar_1[j][2 * i]
            temp1_Im = data_polar_1[j][2 * i + 1]
            temp2_Re = data_polar_2[j][2 * i]
            temp2_Im = data_polar_2[j][2 * i + 1]

            amplitude_polar_1[j][i] = 10 * math.log10((temp1_Re ** 2) + (temp1_Im ** 2)) - offset
            amplitude_polar_2[j][i] = 10 * math.log10((temp2_Re ** 2) + (temp2_Im ** 2)) - offset
            total_gain[j][i] = 10 * math.log10(((temp2_Re ** 2 + temp1_Re ** 2) + (temp2_Im ** 2 + temp1_Im ** 2))) - offset

            #  Draw a simple plot to have a quickview on the results
        s1 = total_gain[0, :]
        line_array[vertical_angle_idx][0].set_ydata(s1)

        s2 = total_gain[1, :]
        line_array[vertical_angle_idx][1].set_ydata(s2)

        s3 = total_gain[2, :]
        line_array[vertical_angle_idx][2].set_ydata(s3)

        s4 = total_gain[3, :]
        line_array[vertical_angle_idx][3].set_ydata(s4)

        s5 = total_gain[4, :]
        line_array[vertical_angle_idx][4].set_ydata(s5)

        s6 = total_gain[5, :]
        line_array[vertical_angle_idx][5].set_ydata(s6)

        fig.canvas.draw()
        fig.canvas.flush_events()

        # Total Amplitude plot
        # plt.clf()
        # plt.plot(angles_list, s1, label='Port 1', lw=1)
        # plt.plot(angles_list, s2, label='Port 2', lw=1)
        # plt.plot(angles_list, s3, label='Port 3', lw=1)
        # plt.plot(angles_list, s4, label='Port 4', lw=1)
        # plt.plot(angles_list, s5, label='Port 5', lw=1)
        # plt.plot(angles_list, s6, label='Port 6', lw=1)
        # plt.plot(angles_list, s7, label='Port 7', lw=1)
        # plt.plot(angles_list, s8, label='Port 8', lw=1)
        # plt.ylim((0, 30))
        # plt.title('Total Gain')
        # plt.xlabel('Phi (degree)')
        # plt.ylabel('Mag (dB)')
        # plt.legend(loc='best')
        # plt.grid()
        # plt.draw()

    # print('Return to home')
    # gcs.GOH()
    # pitools.waitontarget(gcs, axis)
    # mbx.gim_move(0, FIX_H_ANGLE, 0)
    # mbx.wait_stop_moving()



    #  Export the calculated data as CSV file for each measured port
    for j in range(len(correlator_port_1_list)):
        np.savetxt(filename + '_DATA_polar_1_port_' + str(j) + '.csv', amplitude_polar_1[j], delimiter=';')
        np.savetxt(filename + '_DATA_polar_2_port_' + str(j) + '.csv', amplitude_polar_2[j], delimiter=';')
        np.savetxt(filename + '_DATA_Total_Gain_port_' + str(j) + '.csv', total_gain[j], delimiter=';')

    # Export the list of angles
    np.savetxt(filename + '_DATA_angle.csv', angles_list, delimiter=';')

    #  Draw a simple plot to have a quickview on the results
    s1 = total_gain[0, :]
    s2 = total_gain[1, :]
    s3 = total_gain[2, :]
    s4 = total_gain[3, :]
    s5 = total_gain[4, :]
    s6 = total_gain[5, :]
    #s7 = total_gain[6, :]
    #s8 = total_gain[7, :]

    #  Draw a simple plot to have a quickview on the results
    u1 = amplitude_polar_1[0, :]
    u2 = amplitude_polar_1[1, :]
    u3 = amplitude_polar_1[2, :]
    u4 = amplitude_polar_1[3, :]
    u5 = amplitude_polar_1[4, :]
    u6 = amplitude_polar_1[4, :]

    # Total Amplitude plot
    # plt.plot(angles_list, s1, label='Port 1', lw=1)
    # plt.plot(angles_list, s2, label='Port 2', lw=1)
    # plt.plot(angles_list, s3, label='Port 3', lw=1)
    # plt.plot(angles_list, s4, label='Port 4', lw=1)
    # plt.plot(angles_list, s5, label='Port 5', lw=1)
    # plt.plot(angles_list, s6, label='Port 6', lw=1)
    #plt.plot(angles_list, s7, label='Port 7', lw=1)
    #plt.plot(angles_list, s8, label='Port 8', lw=1)
    # plt.ylim((0,30))
    # plt.title('Total Gain')
    # plt.xlabel('Phi (degree)')
    # plt.ylabel('Mag (dB)')
    # plt.legend(loc='best')
    # plt.ioff()
    # plt.grid()
    # plt.show()

path_full = filename + '_plot.png'
# plt.savefig(path_full, dpi=300)
plt.ioff()
# plt.grid()
plt.show()



# Close the session
instr.close()
correlator.close()
mbx.close()
