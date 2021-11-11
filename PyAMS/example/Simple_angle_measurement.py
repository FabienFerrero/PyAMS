import math
from math import sqrt

import matplotlib.pyplot as plt
from RsInstrument.RsInstrument import RsInstrument
from RsInstrument import *  # The RsInstrument package is hosted on pypi.org, see Readme.txt for more details
from time import time
import numpy as np
from random import uniform
from pipython import GCSDevice, pitools


from pipython import GCSDevice

gcs = GCSDevice('C-863.12')
gcs.InterfaceSetupDlg()
print('connected: {}'.format(gcs.qIDN().strip()))
axis = 1


print('===========================================================================')
print('============= TASK 1 : An ETHERNET connection is established between your PC and the ZNA instrument ...')
print('===========================================================================')
instr = None
try:
	instr = RsInstrument('TCPIP::169.254.202.203::INSTR', True, True) # Initializing the session
	instr.visa_timeout = 10000  # Timeout for VISA Read Operations -délai d'attente-
	instr.opc_timeout = 100000  # Timeout for opc-synchronised operations
	instr.instrument_status_checking = True  # Error check after each command (fetch on désactive les erreurs == >
	instr.opc_query_after_write = True

except Exception as ex:
	print('Error initializing the instrument session:\n' + ex.args[0])
	exit()

# +++++++++++++++++++++++++++++++ OPTIONS ++++++++++++++++++++++++++++++++++++++++++++
# resource_string_1 = 'TCPIP::169.254.202.203::INSTR'  # Standard LAN connection (also called VXI-11)

print('')
print('... DONE !')
print('')

print('============================================================================')
print('============= TASK 2 : Access to identification properties of ZNA instrument ...')
print('============================================================================')
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
print('')
print('... DONE !')
print('')

print('===========================================================================')
print('============= TASK 3 : Configuration of Parameters ... ')
print('===========================================================================')
instr.clear_status() # Pour effacer toutes les erreurs du sous-système d'état de l'instrument
instr.write_str('*RST')
instr.write_str('FREQ:STARt 24 GHZ')
instr.write_str('FREQ:STOP  28 GHZ')
instr.write_str('DISP:WIND:TRAC:Y:RLEV 0.0')       #  the Reference Level
instr.write_str('BAND 1 kHz')                       #  the RBW
instr.write_str('SYSTEM:DISPLAY:UPDATE ON')

# +++++++++++++++++++++++++++++++ OPTIONS ++++++++++++++++++++++++++++++++++++++++++++
#instr.reset()
#instr.write_str('INITiate1:CONTinuous ON')
#instr.write_str('INIT1:CONT OFF')  # Switch OFF the continuous sweep (Aucun signal sur la figure) **************************
#instr.write_str('SYST:DISP:UPD ON')
#instr.write_str('SENSe1:FREQuency:STARt 1 GHz; STOP 5.5 GHz')               #  the center frequency
#instr.write_str('FREQ:CENT 28.0 GHz')
instr.write_str('FREQ:SPAN 100 MHz')                #  the span
#instr.write_str_with_opc('INIT:IMM:DUMM')

print('')
print('... DONE !')
print('')

instr.VisaTimeout = 10000  # Sweep timeout - set it higher than the instrument acquisition time
instr.write_str('INIT1', 50000)


print('===========================================================================')
print('============= TASK 4 : MOVE & TRACE S - Parameters ... ')
print('===========================================================================')

t = time() # Start Time

instr.write_str('DISPLAY:WINDOW1:TRACE1:DELETE')
instr.write_str('SOURce1:PATH1:DIRectaccess B16')
instr.write_str('SOURce1:PATH2:DIRectaccess B16')
instr.write_str('DISP:WIND1:STAT ON')

instr.write_str('SWE:POIN 21') # nombre d'échantillon


# ====== "Ch1Tr1", "B2/A1D1" (PORT 1) ..... en dB
instr.write_str('CALC1:PAR:SDEF "Ch1Tr1", "B2/A1D1"') # calcul parametre S= B2/A1, nom : Ch1Tr1
instr.write_str('CALC1:FORM  MLOGarithmic; :DISP:WIND1:TRAC2:FEED "Ch1Tr1"') # Afiichage fig; format : phase;
#instr.write_str('CALC1:FORM  PHASe; :DISP:WIND:TRAC2:FEED "Ch1Tr1"')
#instr.write_str('SWE:AXIS:FREQ ' Port 1; Source'')

# ===== "Ch1Tr2", "B2D2/A2D2" (PORT 2) ..... en dB
instr.write_str('CALC2:PAR:SDEF "Ch1Tr2","B2D2/A2D2"') # calcul parametre S= B2/A1, nom : Ch1Tr1
instr.write_str('CALC2:FORM  MLOGarithmic; :DISP:WIND1:TRAC3:FEED "Ch1Tr2"') # Afiichage fig; format : phase
#instr.write_str('CALC1:FORM  PHASe; :DISP:WIND:TRAC3:FEED "Ch1Tr2"')


angle_min = -40
angle_max = 40
angle_step = 1
angles_list = np.arange(angle_min, angle_max+1, angle_step)
nb_points = len(angles_list)
print("nb_points:")
print(nb_points)
print("angles_list:")
print(angles_list)

trace1 = []
trace2 = []


# Begin measurement at angle_min position
gcs.SVO (axis, 1)
REFMODE = ('FNL',1) # ?

gcs.MVR(axis, float(angle_min))
pitools.waitontarget(gcs, axis)


for i in range(angle_min, angle_max+1, angle_step):
    print("Measure...")
    # Trace 1
    instr.write_str(':CALCULATE1:PARAMETER:SELECT "Ch1Tr1"')
    temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH1DATA', 50000)# récupérer un tableau de flottant
    trace1.append(temp[20:22])

    # Trace 2
    instr.write_str(':CALCULATE2:PARAMETER:SELECT "Ch1Tr2"')
    temp = instr.query_bin_or_ascii_float_list('FORM ASCII; :TRAC? CH2DATA', 50000)# récupérer un tableau de flottant
    trace2.append(temp[20:22])

    # Preparing for next measurement
    print("Changing angle")
    gcs.MVR(axis, float(angle_step))
    pitools.waitontarget(gcs, axis)


# Return to middle position of the angle range, should be changed to return to a ref position
# At the begining of the script, the setup shoud verify (go to) a home ref position
print('Return to home')
home = (nb_points/2)*angle_step
gcs.MVR(axis, -home)
pitools.waitontarget(gcs, axis)

# Calculation
s1 = [] # Amplitude poralization 1
s2 = [] # Amplitude poralization 2
s3 = [] # Phase Polarization 1
s4 = [] # Phase Polarization 2


for i in range(nb_points):
    temp1_Re = trace1[i][0]
    temp1_Im = trace1[i][1]
    temp2_Re = trace2[i][0]
    temp2_Im = trace2[i][1]

    s1.append(20*math.log10(sqrt((temp1_Re**2) + (temp1_Im**2))))
    s2.append(20*math.log10(sqrt((temp2_Re**2) + (temp2_Im**2))))
    s3.append(math.atan2(temp1_Re, temp1_Im)*(180/math.pi))
    s4.append(math.atan2(temp2_Re, temp2_Im)*(180/math.pi))

np.savetxt('ANGLES.txt', angles_list)
np.savetxt('DATA_s1.txt', s1)
np.savetxt('DATA_s2.txt', s2)
np.savetxt('DATA_s3.txt', s3)
np.savetxt('DATA_s4.txt', s4)


#Display of some plots
plt.figure() # fig 1
plt.subplot(2,2,1)
plt.plot(angles_list,s1,label='Mag_Polar1', lw=1)
plt.plot(angles_list,s2,label='Mag_Polar2', lw=1)
plt.title('Amplitude des deux polars à 0deg - 0dB')
plt.ylabel('Mag (dB)')
plt.legend()
plt.grid()
plt.subplot(2,2,3)
plt.plot(angles_list,s3,label='Phase_Polar1', lw=1)
plt.plot(angles_list,s4,label='Phase_Polar2', lw=1)
plt.title('Phase des deux polars à 0deg - 0dB')
plt.xlabel('Phi (degré)')
plt.ylabel('Phase (degré)')
plt.legend()
plt.grid()
plt.subplot(2,2,2)
plt.plot(angles_list,s1,label='Mag_Polar1', lw=2)
plt.title('Amplitude polar 1 à 0deg - 0dB')
plt.ylabel('Mag (dB)')
plt.legend()
plt.grid()
plt.subplot(2,2,4)
plt.plot(angles_list,s3,label='Phase_Polar1', lw=2)
plt.title('Phase polar 1 à 0deg - 0dB')
plt.xlabel('Phi (degré)')
plt.ylabel('Phase (degré)')
plt.legend()
plt.grid()
plt.show()

# Close the session
instr.close()
