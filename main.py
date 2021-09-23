from Packets import Packets
from configparser import ConfigParser
import ifaddr
import socket
import os


config = ConfigParser()
config.read('./config.ini')


def GetIp(interface):
    adapters = ifaddr.get_adapters()

    temp = ""
    for adapter in adapters:
        if (adapter.nice_name == interface):
            temp = adapter.ips[0].ip
            print(interface + "--------------------------->", temp)
    
    return temp


# delete "sample.txt"
if os.path.exists("./sample.txt"):
    os.remove("./sample.txt")


# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = (GetIp(config['GENERAL']['InterfaceRasp']), int(config['GENERAL']['PortRasp']))
s.bind(server_address)

count=0

while True:
    print("####### Node is listening #######")
    data, address = s.recvfrom(8192)

    packet = Packets.getPacketFromBytes(data)
    #print (packet.printLitePacket())
    print("--->", GetIp(config['GENERAL']['InterfaceRasp']))

    if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
        if(int(packet.Type) == 2):
            print("Data Received from: ", packet.Source)
            #if count==1024:
            #    os.remove("./{}.txt".format(packet.Source))
            #    count=0
            elements = bytearray(packet.Payload)
            #del elements[::3] # every 3 chars it has the synch character to be deleted
            f = open("/dev/shm/{}.bin".format(packet.Source), "ab")
            #f.write(elements)

            i = 0
            last_sample = b'\x00\x00'
            while i < len(elements) - 2:
                if elements[i] == 48:
                    #Next is a sample
                    if elements[i+1] != 48 and elements[i+2] != 48:
                        f.write(elements[i+1:i+3])
                        last_sample = elements[i+1:i+3]
                        i += 2
                    #Next is not a sample
                    else:
                        #Resend the last sample and move on
                        f.write(last_sample)
                        if elements[i+1] == 48:
                            i += 1
                        else:
                            i += 2
                #If it is not a 48 move on
                else:
                    i += 1
            f.close()
            count+=1
            print("packet count: "+str(count))
