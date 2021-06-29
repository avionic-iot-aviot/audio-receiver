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
            print(interface + "--------------------------->", temp)
    
    return temp


# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = (GetIp(config['GENERAL']['InterfaceRasp']), config['GENERAL']['PortRasp'])
s.bind(server_address)

while True:
    print("####### Node is listening #######")
    data, address = s.recvfrom(8192)

    packet = Packets.getPacketFromBytes(data)
    print (packet.printLitePacket())
    print("--->", GetIp(config['GENERAL']['InterfaceRasp']))

    if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
        if(int(packet.Type) == 2):
            print("Data Received from: ", packet.Source)
            f = open("./sample.txt", "wb")
            f.write(packet.Payload)
            f.close()
