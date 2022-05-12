import time


def select_port(common, port):
    common_str = str(common)
    port_str = str(port)
    # Check if we must add a '0'
    if port < 10:
        return 'S' + common_str + '0' + port_str
    else:
        return 'S' + common_str + port_str


def change_port(correlator, common, port):
    data_to_send = select_port(common, port)
    correlator.write(data_to_send.encode('ascii'))
    print("Command sent: ", data_to_send)


# We can't use the sleep function because it relies on the OS clock which is not precise enough in Windows environments
# (approx. 16ms) Instead we create a Delay_ms function which use time.perf_counter() which use the most precise clock
# available on the system (less than 1ms)

def delay_ms(ms):
    t1 = time.perf_counter()
    t2 = t1
    while ((t2 - t1) * 10 ** 3) < ms:
        t2 = time.perf_counter()
    # print("Elapsed time: %.f ms" % ((t2 - t1) * 10 ** 3))
    print(f'Elapsed time : {((t2 - t1) * 10 ** 3):.2f}')
    return (t2 - t1) * 10 ** 3


def sweep_port(correlator, start, stop, common_port, time_interval):
    if type(start) != int or type(stop) != int:
        return "start and stop values must be integers."
    if start > stop:
        return "Start port must be inferior to stop port."
    if type(common_port) != int:
        return "common_port value must be an integer."
    if time_interval < 0.4:
        return "Baudrate limit exceeded, increase the time interval."

    print("Parameters :")
    print("Common port :", common_port)
    print("sweep start port :", start)
    print("sweep stop port :", stop)
    print("time interval :", time_interval, " ms")

    for i in range(start, stop + 1):
        data_to_send = select_port(common_port, i)
        correlator.write(data_to_send.encode('ascii'))
        print("Command sent: ", data_to_send)
        delay_ms(time_interval)


def sweep_dual(correlator, start, stop, common_port_1, common_port_2, time_interval):
    sweep_port(correlator, start, stop, common_port_1, time_interval)
    delay_ms(time_interval)
    sweep_port(correlator, start, stop, common_port_2, time_interval)
