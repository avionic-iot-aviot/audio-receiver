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

count=0

while True:
    ##print("####### Node is listening #######")
    data, address = s.recvfrom(8192)

    packet = Packets.getPacketFromBytes(data)

    if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
        if(int(packet.Type) == 2):
            elements = bytearray(packet.Payload)
            bytes_to_write = bytearray()
            temp_bytes = bytearray()
            bytes_effectively_written = 0

            i = 0
            while i < len(elements):
                element_as_int = int.from_bytes(elements[i:i+1],"big", signed="True")
                if element_as_int != 48:
                    temp_bytes.extend(elements[i:i+1])
                elif element_as_int == 48:
                    if len(temp_bytes) == 2:
                        bytes_to_write.extend(temp_bytes[0:2])
                        bytes_effectively_written += 2
                    elif len(temp_bytes) > 2:
                        print("audio-receiver: I have more than 2 bytes")
                    temp_bytes = bytearray()
                i += 1
            
            
            
            if len(bytes_to_write) > 0:
                # We don't write if we are not receiving (or 5 times neutral writing have been executed)  
                #print("Byte-Writer: byte sent ", len(bytes_to_write))
                f = open("/dev/shm/{}.bin".format(packet.Source), "ab")
                f.write(bytes_to_write)
                f.close()
            
            print("audio-receiver: Data Received from: ", packet.Source, ' Size: ', len(elements), ' Effect: ', bytes_effectively_written)
            
            count+=1
            ##print("audio-receiver: packet count "+str(count))
