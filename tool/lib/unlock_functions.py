import struct

def example(seed):
    seed=struct.unpack("L",bytes(seed))[0] #Assumes 4 bytes seed
    seed+=0x42
    return list(bytearray(struct.pack("L",seed)))