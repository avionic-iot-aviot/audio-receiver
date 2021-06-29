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
    print (packet.printLitePacket())
    print("--->", GetIp(config['GENERAL']['InterfaceRasp']))

    if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
        if(int(packet.Type) == 2):
            print("Data Received from: ", packet.Source)
            if count==100:
                os.remove("./sample.txt")
                count=0
            f = open("./sample.txt", "ab")
            f.write(packet.Payload)
            f.close()
            count+=1
            print("packet count: "+str(count))