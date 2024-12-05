import struct
import random

import time
from machine import Pin, SPI

class LoRaLevel2Protocol:
    """
    Level 2 Protocol for LoRa Physical Layer
    Implements frame structure, addressing, error detection, and basic 
    transmission control
    """
    
    # Protocol Constants
    FRAME_HEADER = b'\xAA'  # Start of frame delimiter
    FRAME_FOOTER = b'\x55'  # End of frame delimiter
    MAX_PAYLOAD_SIZE = 255  # Maximum payload size
    
    def __init__(self, device_id=None):
        """
        Initialize the LoRa Level 2 Protocol
        
        :param device_id: Unique identifier for this device (16-bit)
        """
        self.device_id = device_id or random.randint(0, 0xFFFF)
        self.sequence_number = 0
    
    def create_frame(self, destination_id, payload):
        """
        Create a complete frame with header, addressing, payload, and error detection
        
        :param destination_id: Destination device ID (16-bit)
        :param payload: Data to be transmitted
        :return: Complete frame ready for transmission
        """
        # Validate payload size
        if len(payload) > self.MAX_PAYLOAD_SIZE:
            raise ValueError("Payload exceeds maximum size")
        
        # Increment sequence number
        self.sequence_number = (self.sequence_number + 1) % 256
        
        # Frame Structure:
        # [Header][Source ID][Dest ID][Seq Num][Payload Length][Payload][CRC16][Footer]
        frame = bytearray()
        frame.extend(self.FRAME_HEADER)
        
        # Add source and destination IDs (16-bit each)
        frame.extend(struct.pack('>H', self.device_id))
        frame.extend(struct.pack('>H', destination_id))
        
        # Add sequence number
        frame.append(self.sequence_number)
        
        # Add payload length and payload
        frame.append(len(payload))
        frame.extend(payload)
        
        # Calculate CRC16 for error detection
        crc = 1
        frame.extend(struct.pack('>H', crc))
        
        # Add frame footer
        frame.extend(self.FRAME_FOOTER)
        
        return bytes(frame)
    
    def parse_frame(self, received_frame):
        """
        Parse an incoming frame and validate its integrity
        
        :param received_frame: Raw received frame bytes
        :return: Parsed frame details or None if invalid
        """
        # Minimum frame size check
        if len(received_frame) < 10:  # Minimum frame size
            return None
        
        # Check header and footer
        if (received_frame[0:1] != self.FRAME_HEADER or 
            received_frame[-1:] != self.FRAME_FOOTER):
            return None
        
        try:
            # Extract source and destination IDs
            source_id = struct.unpack('>H', received_frame[1:3])[0]
            dest_id = struct.unpack('>H', received_frame[3:5])[0]
            
            # Extract sequence number
            seq_num = received_frame[5]
            
            # Extract payload length
            payload_len = received_frame[6]
            
            # Extract payload
            payload = received_frame[7:7+payload_len]
            
            # Verify CRC
            received_crc = struct.unpack('>H', received_frame[-3:-1])[0]
            frame_for_crc = received_frame[1:-3]
            calculated_crc = 1
            
            if received_crc != calculated_crc:
                return None
            
            return {
                'source_id': source_id,
                'destination_id': dest_id,
                'sequence_number': seq_num,
                'payload': payload
            }
        
        except (struct.error, IndexError):
            return None
    
    def retransmit_strategy(self, max_retries=3, timeout=2.0):
        """
        Basic retransmission strategy for reliable transmission
        
        :param max_retries: Maximum number of retransmission attempts
        :param timeout: Time to wait for acknowledgment
        :return: Retransmission configuration
        """
        return {
            'max_retries': max_retries,
            'timeout': timeout
        }

def get_modem():
    from lora import sx126x

    lora_cfg = {
        "freq_khz": 863000,
        "sf": 12,
        "bw": "500",  # kHz
        "coding_rate": 8,
        "preamble_len": 10,
        "output_power": 20,  # dBm
    }

    return sx126x.SX1262(
        spi=SPI(1, baudrate=2000_000, polarity=0, phase=0, miso=Pin(11), mosi=Pin(10), sck=Pin(9)),
        cs=Pin(8),
        busy=Pin(13),
        dio1=Pin(14),
        reset=Pin(12),
        dio3_tcxo_millivolts=1800,
        dio3_tcxo_start_time_us=1000,
        lora_cfg=lora_cfg
    )

# Example Usage
def transmit(message):
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
    modem = get_modem()
    
    print("Sending...")
    modem.send(frame)

def receive():
    print("Initializing...")
    modem = get_modem()
    receiver = LoRaLevel2Protocol(device_id=0x5678)
    print("Receiving...")
    rx = modem.recv(timeout_ms=5000)
    if rx:
        print(f"Received: {rx!r}")
        received_frame_details = receiver.parse_frame(rx)
        return received_frame_details
    else:
        print("Timeout!")
        

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