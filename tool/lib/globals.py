import can
from can.interfaces.pcan import PcanBus

def initialize(): 
    global bus 
    global DEFAULT_INTERFACE
    global pad
    global pcan
    global canfd
    bus = None
    DEFAULT_INTERFACE = None
    pad=False
    pcan=False
    canfd=False

def get_bus():
    if pcan:
        if canfd:
            bus = PcanBus(fd=True, f_clock=80000000,nom_brp=2, nom_tseg1=63, nom_tseg2=16, nom_sjw=16,data_brp=2, data_tseg1=15, data_tseg2=4, data_sjw=4)
        else:
            bus = PcanBus()
    else:
        bus = can.Bus(DEFAULT_INTERFACE)
    return bus