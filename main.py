import time
from Packets import Packets
from configparser import ConfigParser
import ifaddr
import socket
import threading
from queue import Queue


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

# VARIABLES

sample_size_in_bytes = 2
samples_rate_per_seconds = 6000 #Samples per seconds in bytes
bytes_per_seconds = samples_rate_per_seconds * sample_size_in_bytes

emitted_samples_per_loop = 600 # Desidered number we decided
emitted_bytes_per_loop = emitted_samples_per_loop * sample_size_in_bytes

writer_sleep_time = emitted_bytes_per_loop / bytes_per_seconds #in seconds

NEUTRAL_BYTE_VALUE = b'/x31'

#expected_bytes_to_write = samples_rate_per_seconds * writer_sleep_time * sample_size_in_bytes #bytes needed to be written when the writer thread awakes

class ThreadUDPReceiver(threading.Thread):
    def __init__(self, name, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        
    def run(self):
        print('UDP-RECEIVER started')
        # Create a UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to the port
        server_address = (GetIp(config['GENERAL']['InterfaceRasp']), int(config['GENERAL']['PortRasp']))
        s.bind(server_address)

        count=0

        while True:
            #print("####### Node is listening #######")
            data, address = s.recvfrom(8192)

            packet = Packets.getPacketFromBytes(data)
            #print (packet.printLitePacket())
            #print("--->", GetIp(config['GENERAL']['InterfaceRasp']))

            if (packet.Destination == GetIp(config['GENERAL']['InterfaceRasp'])):
                if(int(packet.Type) == 2):
                    elements = bytearray(packet.Payload)
                    print("UDP-RECEIVER: Data Received from: ", packet.Source, ' Size: ', len(elements))
                    temp_bytes = bytearray()

                    i = 0
                    while i < len(elements):
                        if elements[i] != 48:
                            temp_bytes.extend(elements[i])
                        else:
                            if len(temp_bytes) >= 2:
                                self.queue.put(temp_bytes[0])
                                self.queue.put(temp_bytes[1])
                            elif len(temp_bytes) == 1:
                                self.queue.put(temp_bytes[0])
                                self.queue.put(temp_bytes[0])
                            elif len(temp_bytes) == 0:
                                self.queue.put(NEUTRAL_BYTE_VALUE)
                                self.queue.put(NEUTRAL_BYTE_VALUE)
                            temp_bytes = bytearray()
                        i += 1
                    
                    count+=1
                    print("UDP-RECEIVER: packet count "+str(count))


class ThreadByteWriter(threading.Thread):
    def __init__(self, name, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.times_queue_was_empty = 0 #needed to avoid having the writer writing 0s every loop
        
    def run(self):
        print("Byte-Writer started")
        while True:
            time.sleep(writer_sleep_time)
            bytes = bytearray()
            
            if self.queue.empty():
                self.times_queue_was_empty += 1
                # If the queue was not empty, it writes neutral bytes (for maximum 5 times)
                if self.times_queue_was_empty < 5:
                    print("Byte-Writer: Queue is empty! I'm sending neutral bytes.")
                    bytes.extend(NEUTRAL_BYTE_VALUE * emitted_bytes_per_loop)
            
            # We have bytes in the queue
            elif not self.queue.empty():
                self.times_queue_was_empty = 0
                
                # Reading from the queue until I have all the bytes I need or it is not empty 
                while not self.queue.empty() or len(bytes) < emitted_bytes_per_loop:
                    byte = self.queue.get()
                    bytes.extend(byte)
                
                
                bytes_i_have_extracted_from_queue = len(bytes)
                print("Byte-Writer: received bytes ", bytes_i_have_extracted_from_queue, " out of ", emitted_bytes_per_loop)
                
                # We check whether the bytes array is smaller than expected. In that case we fill it with neutral bytes.
                if bytes_i_have_extracted_from_queue < emitted_bytes_per_loop:
                    diff = emitted_bytes_per_loop - bytes_i_have_extracted_from_queue
                    bytes.extend(NEUTRAL_BYTE_VALUE * diff)            
            
            
            if len(bytes) > 0:
                # We don't write if we are not receiving (or 5 times neutral writing have been executed)  
                f = open("/dev/shm/192.168.3.3.bin", "ab")
                f.write(bytes)
                f.close()
            else:
                # We want to prevent overflowing for this variable, when the micr is off
                self.times_queue_was_empty = 6



# MAIN

queue19216833 = Queue()
threadUDPReceiver = ThreadUDPReceiver("UDPReceiverThread", queue19216833)
threadByteWriter = ThreadByteWriter("ByteWriterThread", queue19216833)

threadUDPReceiver.start()
threadByteWriter.start()