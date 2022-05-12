import math
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from time import time
from RsInstrument.RsInstrument import RsInstrument
from pipython import GCSDevice, pitools
import serial
import Correlator_lib

# Path to save the plots
path = "results/"

# Configure file name
num_meas = '220315'
AUT = 'Dipoles_28'

# Configure scan
angle_min = -35.0
angle_max = 35.0
angle_step = 0.5
correlator_port_1_list = [2, 3, 4, 5]  # Output ports of the correlator to measure on common port 1 of the correlator

# Correlator related parameters
nb_common_ports = 4
nb_ports = 16
time_interval = 250  # in milliseconds

#  Connection to the correlator
print("Connecting correlator")
correlator = serial.Serial('COM6', 100000)
print("Correlator connected !")

#  Connection to the stepper motor controller
gcs = GCSDevice('C-863.12')
gcs_sn = "0021550330"

print("Connecting GCS")
gcs.ConnectUSB(gcs_sn)
print('GCS connected: {}'.format(gcs.qIDN().strip()))
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
instr.write_str('FREQ:STARt 28 GHZ')
instr.write_str('FREQ:STOP  33 GHZ')
instr.write_str('FREQ:SPAN 100 MHz')
instr.write_str('BAND 1 kHz')  # RBW
instr.write_str('DISP:WIND:TRAC:Y:RLEV 0.0')  # Reference Level
instr.write_str('SYSTEM:DISPLAY:UPDATE ON')

print('\n VNA Configured !\n')

instr.write_str('INIT1')

t = time()  # Start Time

instr.write_str('DISPLAY:WINDOW1:TRACE1:DELETE')
instr.write_str('SOURce1:PATH1:DIRectaccess B16')
instr.write_str('SOURce1:PATH2:DIRectaccess B16')
instr.write_str('DISP:WIND1:STAT ON')
instr.write_str('SWE:POIN 50')  # Sweep points

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

#  Customize the filename
info_measure = num_meas + AUT
filename = path + info_measure + '_' + str(angle_min) + '_' + str(angle_max) + '_' + str(angle_step)

gcs.SVO(axis, 1)  # Set servo ON
gcs.GOH()  # Go to the home position
pitools.waitontarget(gcs, axis)
print("Homing complete !")
Correlator_lib.delay_ms(2500)  # Wait a bit before the measurement begin

gcs.MOV(axis, angle_min)  # Begin measurement at angle_min position
pitools.waitontarget(gcs, axis)
print("Initial position Complete !")

#  Create 2 multidimensional arrays to store the measurements data
data_polar_1 = np.zeros((len(correlator_port_1_list), len(angles_list) * 2))
data_polar_2 = np.zeros((len(correlator_port_1_list), len(angles_list) * 2))

for i in range(len(angles_list)):
    Correlator_lib.delay_ms(750)  # Delay
    print("Measure...")

    for j in range(len(correlator_port_1_list)):
        # Selecting the port on the correlator
        Correlator_lib.change_port(correlator, 1, correlator_port_1_list[j])
        Correlator_lib.delay_ms(250)  # Delay
        # Trace 1
        instr.write_str(':CALCULATE1:PARAMETER:SELECT "Ch1Tr1"')
        temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH1DATA')
        data_polar_1[j][2 * i] = temp[25]  # Re
        data_polar_1[j][2 * i + 1] = temp[27]  # Im

        # Trace 2
        instr.write_str(':CALCULATE2:PARAMETER:SELECT "Ch1Tr2"')
        temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH2DATA')
        data_polar_2[j][2 * i] = temp[25]  # Re
        data_polar_2[j][2 * i + 1] = temp[27]  # Im

    # Preparing for next measurement
    print(f'Changing angle {i}/{len(angles_list)}, {(i / len(angles_list) * 100):.0f} %')
    gcs.MVR(axis, angle_step)  # Move to the next angle
    pitools.waitontarget(gcs, axis)

print('Return to home')
gcs.GOH()
pitools.waitontarget(gcs, axis)

# Calculation
# Create multidimensional arrays to store the results of the calculations for each measured port
amplitude_polar_1 = np.zeros((len(correlator_port_1_list), len(angles_list)))
amplitude_polar_2 = np.zeros((len(correlator_port_1_list), len(angles_list)))
total_gain = np.zeros((len(correlator_port_1_list), len(angles_list)))

for i in range(nb_points):
    for j in range(len(correlator_port_1_list)):
        temp1_Re = data_polar_1[j][2 * i]
        temp1_Im = data_polar_1[j][2 * i + 1]
        temp2_Re = data_polar_2[j][2 * i]
        temp2_Im = data_polar_2[j][2 * i + 1]

        amplitude_polar_1[j][i] = 20 * math.log10(sqrt((temp1_Re ** 2) + (temp1_Im ** 2)))
        amplitude_polar_2[j][i] = 20 * math.log10(sqrt((temp2_Re ** 2) + (temp2_Im ** 2)))
        total_gain[j][i] = 20 * math.log10(sqrt(((temp2_Re ** 2 + temp1_Re ** 2) + (temp2_Im ** 2 + temp1_Im ** 2))))

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

# Amplitude plot
plt.plot(angles_list, s1, label='Port 1', lw=1)
plt.plot(angles_list, s2, label='Port 2', lw=1)
plt.plot(angles_list, s3, label='Port 3', lw=1)
plt.plot(angles_list, s4, label='Port 4', lw=1)
plt.title('Total Gain')
plt.xlabel('Phi (degree)')
plt.ylabel('Mag (dB)')
plt.legend(loc='best')
plt.grid()

path_full = filename + '_plot.png'
plt.savefig(path_full, dpi=300)
plt.close()

# Close the session
instr.close()
correlator.close()
