import time
from Packets import Packets
from configparser import ConfigParser
import ifaddr
import socket


config = ConfigParser()
config.read('./config.ini')

def GetIp(interface):
    adapters = ifaddr.get_adapters()

    temp = ""
    for adapter in adapters:
        if (adapter.nice_name == interface):
            temp = adapter.ips[0].ip
    
    return temp



print('audio-receiver started')
# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = (GetIp(config['GENERAL']['InterfaceRasp']), int(config['GENERAL']['PortRasp']))
s.bind(server_address)
volume_multiplier = 12

while True:
    ##print("####### Node is listening #######")
    data, address = s.recvfrom(8192)
    if len(data) < 5:
        try:
            new_volume_multiplier = int(data)
            if 1 < new_volume_multiplier < 50:
                volume_multiplier = new_volume_multiplier
            elif new_volume_multiplier <= 1:
                volume_multiplier = 1
            else:
                volume_multiplier = 50
            print("New volume multiplier is: {}".format(volume_multiplier))
        except:
            print("Received a wrong value for volume_multiplier.")
        continue
    packet = Packets.getPacketFromBytes(data)

    if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
        if(int(packet.Type) == 2):
            elements = bytearray(packet.Payload)
            bytes_to_write = bytearray()
            temp_bytes = bytearray()
            bytes_effectively_written = 0

            i = 0
            # The format of the bytes in the packet is as follow:
            # 0 s1msb s1lsb 0 s2msb s2lsb 0 .... 0 sNmsb sNlsb
            while i < len(elements):
                if elements[i] != 48: # our separator is b'/x30' which is 48 in ASCII (literal '0')
                    temp_bytes.extend(elements[i:i+1])
                    
                elif elements[i] == 48:
                    if len(temp_bytes) == 2:
                        integer = int.from_bytes(temp_bytes, "big", signed="True")
                        integer *= volume_multiplier
                        try:
                            new_bytes = integer.to_bytes(2, 'big', signed=True)
                        except:
                            if integer > 0:
                                integer = 30000
                            else:
                                integer = -30000
                            new_bytes = integer.to_bytes(2, 'big', signed=True)
                        bytes_to_write.extend(new_bytes)
                        bytes_effectively_written += 2
                    temp_bytes = bytearray()
                i += 1
            
            
            # This is to recover the last sample "sNmsb sNlsb"
            if len(temp_bytes) == 2:
                    bytes_to_write.extend(temp_bytes[0:2])
                    bytes_effectively_written += 2        
            
            if len(bytes_to_write) > 0:
                # We don't write if we are not receiving (or 5 times neutral writing have been executed)  
                #print("Byte-Writer: byte sent ", len(bytes_to_write))
                f = open("/dev/shm/{}.bin".format(packet.Source), "ab")
                f.write(bytes_to_write)
                f.close()
            
            #print("audio-receiver: Data Received from: ", packet.Source, ' Size: ', len(elements), ' Effect: ', bytes_effectively_written)
