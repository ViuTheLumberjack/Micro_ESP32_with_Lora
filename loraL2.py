import struct
import random

import time
from machine import unique_id, Pin, SPI

import crc16

from collections import OrderedDict

class LoRaLevel2Protocol:
    
    # Protocol Constants
    FRAME_HEADER = b'\xAA'  	# Start of frame delimiter
    FRAME_HEADER_ACK = b'\xBB'	# Start of ack frame delimiter
    FRAME_FOOTER = b'\xFF'  	# End of frame delimiter
    MAX_PAYLOAD_SIZE = 255  	# Maximum payload size
    
    def __init__(self):
        self.device_id = unique_id()
        self.sequence_number = 0
        
    def get_sequence_number(self):
        return self.sequence_number
    
    def set_sequence_number(self, sequence_number):
        self.sequence_number = sequence_number
    
    def create_frame(self, payload):
        if len(payload) > self.MAX_PAYLOAD_SIZE:
            raise ValueError("Payload exceeds maximum size")
        self.sequence_number = (self.sequence_number + 1) % 256
        
        # Frame Structure:
        # [Header][Source ID][Seq Num][Payload Length][Payload][CRC16][Footer]
        # Total Overhead size is 1+6+1+1+2+1=12
        
        frame = bytearray()
        frame.extend(self.FRAME_HEADER)
        frame.extend(self.device_id)
        frame.append(self.sequence_number)
        frame.append(len(payload))
        frame.extend(payload)    
        crc = crc16.crc16xmodem(frame[1:])
        frame.extend(struct.pack('>H', crc))
        frame.extend(self.FRAME_FOOTER)
        
        return bytes(frame)
    
    def parse_frame(self, received_frame):
        if len(received_frame) < 12: 
            return None
        
        if (received_frame[0:1] != self.FRAME_HEADER and
            received_frame[0:1] != self.FRAME_HEADER_ACK or
            received_frame[-1:] != self.FRAME_FOOTER):
            return None
        
        if (received_frame[0:1] == self.FRAME_HEADER):
            try:
                source_id = ':'.join(f'{byte:02X}' for byte in received_frame[1:7])
                seq_num = received_frame[7]
                payload_len = received_frame[8]
                payload = received_frame[9:9+payload_len].decode()
                received_crc = received_frame[-3:-1]
                frame_for_crc = received_frame[1:-3]
                calculated_crc = struct.pack('>H', crc16.crc16xmodem(frame_for_crc))
                if received_crc != calculated_crc:
                    return None
                
                return OrderedDict({
                    'Type: ': "DATA",
                    'Source ID: ': source_id,
                    'Sequence Number: ': seq_num,
                    'Payload Lenght: ': payload_len,
                    'Payload: ': payload
                })
            
            except (struct.error, IndexError):
                return None
        else:
            source_id = ':'.join(f'{byte:02X}' for byte in received_frame[1:7])
            dest_id = ':'.join(f'{byte:02X}' for byte in received_frame[7:13])
            sequence_number = received_frame[13]
            return OrderedDict({
                    'Type: ': "ACK",
                    'Source ID: ': source_id,
                    'Destination ID: ': dest_id,
                    'Sequence Number: ': sequence_number
                })
    
    async def transmit(self, message):
        payload = message.encode()
        frame = self.create_frame(payload)
        modem = get_modem()
        
        print("Sending...")
        await modem.send(frame)
        print("Sent!\n")
        
    async def receive(self):
        modem = get_modem()
        print("Receiving...\n")
        rx = await modem.recv(timeout_ms=5000)
        if rx:
            received_frame_details = self.parse_frame(rx)
            return received_frame_details
        else:
            return None
        
    def create_ack_frame(self, sequence_number, dest_id):
        # Frame Structure:
        # [Header][Source ID][Dest ID][Sequence Number][Footer]
        # Total Overhead size is 1+6+6+1+1=15
        
        frame = bytearray()
        frame.extend(self.FRAME_HEADER_ACK)
        frame.extend(self.device_id)
        frame.extend(dest_id)
        frame.append(sequence_number)
        frame.extend(self.FRAME_FOOTER)
        return bytes(frame)
    
    async def transmit_ack(self, sequence_number, dest_id):
        frame = self.create_ack_frame(sequence_number, dest_id)
        modem = get_modem()
        
        print("Sending ACK...")
        await modem.send(frame)
        print("ACK Sent!\n")


def get_modem():
    from lora import AsyncSX1262

    lora_cfg = {
        "freq_khz": 863000,
        "sf": 12,
        "bw": "500",  # kHz
        "coding_rate": 8,
        "preamble_len": 10,
        "output_power": 20,  # dBm
    }

    return AsyncSX1262(
        spi=SPI(1, baudrate=2000_000, polarity=0, phase=0, miso=Pin(11), mosi=Pin(10), sck=Pin(9)),
        cs=Pin(8),
        busy=Pin(13),
        dio1=Pin(14),
        reset=Pin(12),
        dio3_tcxo_millivolts=1800,
        dio3_tcxo_start_time_us=1000,
        lora_cfg=lora_cfg
    )   

def example_transmission():
    """
    Demonstrate basic Level 2 protocol usage
    """
    # Create two device instances
    sender = LoRaLevel2Protocol(device_id=0x1234)
    receiver = LoRaLevel2Protocol(device_id=0x5678)
    
    # Prepare payload
    payload = b'Hello, LoRa World!'
    
    # Create frame
    frame = sender.create_frame(
        destination_id=receiver.device_id, 
        payload=payload
    )
    
    # Here goes the communication
    
    # Simulate frame transmission and reception
    received_frame_details = receiver.parse_frame(frame)
    
    print("Transmission Details:")
    print(f"Source ID: {received_frame_details['source_id']:04X}")
    print(f"Destination ID: {received_frame_details['destination_id']:04X}")
    print(f"Payload: {received_frame_details['payload']}")

# Run the example
if __name__ == '__main__':
    example_transmission()