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
    
    return temp

# VARIABLES

sample_size_in_bytes = 2
samples_rate_per_second = 6000 #Samples per seconds in bytes
bytes_per_second = samples_rate_per_second * sample_size_in_bytes

emitted_samples_per_loop = 600 # Desidered number we decided
emitted_bytes_per_loop = emitted_samples_per_loop * sample_size_in_bytes


writer_sleep_time = emitted_samples_per_loop / samples_rate_per_second #emitted_bytes_per_loop / bytes_per_second #in seconds


NEUTRAL_BYTE_VALUE = b'/x00'

#expected_bytes_to_write = samples_rate_per_second * writer_sleep_time * sample_size_in_bytes #bytes needed to be written when the writer thread awakes

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
                                #self.queue.put(temp_bytes[0:2])
                                bytes_to_write.extend(temp_bytes[0:2])
                                bytes_effectively_written += 2
                            # elif len(temp_bytes) == 1:
                            #     self.queue.put(temp_bytes[0:1] * 2)
                            #     #print("Missing one byte")
                            #     bytes_effectively_written += 2
                            # elif len(temp_bytes) == 0 and i != 0:
                            #     self.queue.put(NEUTRAL_BYTE_VALUE * 2)
                            #     print("UDP-RECEIVER: Missing both the bytes ", i)
                            #     bytes_effectively_written += 2
                            elif len(temp_bytes) > 2:
                                print("UDP-RECEIVER: I have more than 2 bytes")
                            temp_bytes = bytearray()
                        i += 1
                        
                        
                        
                    if len(bytes_to_write) > 0:
                        # We don't write if we are not receiving (or 5 times neutral writing have been executed)  
                        #print("Byte-Writer: byte sent ", len(bytes_to_write))
                        f = open("/dev/shm/{}.bin".format(packet.Source), "ab")
                        f.write(bytes_to_write)
                        f.close()
                    
                    print("UDP-RECEIVER: Data Received from: ", packet.Source, ' Size: ', len(elements), ' Effect: ', bytes_effectively_written)
                    
                    count+=1
                    ##print("UDP-RECEIVER: packet count "+str(count))


class ThreadByteWriter(threading.Thread):
    def __init__(self, name, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.times_queue_was_empty = 0 #needed to avoid having the writer writing 0s every loop
        
    def run(self):
        print("Byte-Writer started")
        while True:
            starting_time = time.time()
            bytes = bytearray()
            
            if self.queue.empty():
                self.times_queue_was_empty += 1
                # If the queue was not empty, it writes neutral bytes (for maximum 5 times)
                if self.times_queue_was_empty < 5:
                    print("Byte-Writer: Queue is empty! I'm sending neutral bytes.")
                    #bytes.extend(NEUTRAL_BYTE_VALUE * emitted_bytes_per_loop)
            
            # We have bytes in the queue
            elif not self.queue.empty():
                self.times_queue_was_empty = 0
                
                # Reading from the queue until I have all the bytes I need or it is not empty 
                while not self.queue.empty() and len(bytes) < emitted_bytes_per_loop:
                    sample = self.queue.get()
                    bytes.extend(sample)
                
                
                bytes_i_have_extracted_from_queue = len(bytes)
                #print("Byte-Writer: received bytes ", bytes_i_have_extracted_from_queue, " out of ", emitted_bytes_per_loop)
                
                # We check whether the bytes array is smaller than expected. In that case we fill it with neutral bytes.
                if bytes_i_have_extracted_from_queue < emitted_bytes_per_loop:
                    #print("Byte-Writer: I was not able to get all the bytes I needed. I got only: ", bytes_i_have_extracted_from_queue, " out of ", emitted_samples_per_loop)
                    diff = emitted_bytes_per_loop - bytes_i_have_extracted_from_queue
                    #bytes.extend(NEUTRAL_BYTE_VALUE * diff)            
            
            
            if len(bytes) > 0:
                # We don't write if we are not receiving (or 5 times neutral writing have been executed)  
                #print("Byte-Writer: byte sent ", len(bytes))
                f = open("/dev/shm/192.168.3.3.bin", "ab")
                f.write(bytes)
                f.close()
            else:
                # We want to prevent overflowing for this variable, when the micr is off
                self.times_queue_was_empty = 6
            ending_time = time.time()
            ##print("Byte-Writer execution time: ", ending_time - starting_time)
            time_spent_during_computation = ending_time - starting_time
            max_between_robe = max(0, writer_sleep_time - time_spent_during_computation)
            if max_between_robe == 0:
                print("Byte-Writer: max was 0")
            time.sleep(max_between_robe)



# MAIN

queue19216833 = Queue()
threadUDPReceiver = ThreadUDPReceiver("UDPReceiverThread", queue19216833)
#threadByteWriter = ThreadByteWriter("ByteWriterThread", queue19216833)

threadUDPReceiver.start()
#threadByteWriter.start()