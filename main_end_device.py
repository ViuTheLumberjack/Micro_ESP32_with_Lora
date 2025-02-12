import loraL2
import asyncio
import time
import machine
import random
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

SCREEN_HEIGHT = 64
SCREEN_WIDTH = 128
LINE_HEIGHT = 8

pin_rst = Pin(21, Pin.OUT)
pin_rst.off()
pin_rst.on()
    
i2c = I2C(0, scl=Pin(18), sda=Pin(17))
oled = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)
oled.fill(0)
cursor = 0

def print_screen(text):
    global cursor
    oled.fill_rect(0, cursor, SCREEN_WIDTH, LINE_HEIGHT, 0)
    oled.text(text, 0, cursor)
    oled.show()
    cursor = (cursor + LINE_HEIGHT) % SCREEN_HEIGHT
    
async def send(lora):
    MAC = ':'.join(f'{byte:02X}' for byte in machine.unique_id())
    base_timeout = 1
    max_retries = 3
    
    while(True):
        try:
            message = str(random.randint(1, 100000000))
            retry_count = 0
            timeout = base_timeout * (2 ** retry_count)
            for i in range(1, max_retries):
                ack_received = False
                if(not ack_received):
                    asyncio.sleep(random.uniform(1, 5))
                    print_screen(f"Invio {message}")
                    await lora.transmit(message)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        ack = await lora.receive()
                        if(ack):
                            if(ack['Type: '] != 'ACK' or ack['Destination ID: '] != MAC or ack['Sequence Number: '] != lora.get_sequence_number()):
                                print_screen("Messaggio ignorato")
                            else:
                                print_screen("ACK ricevuto!")
                                ack_received = True
                                break
                            await asyncio.sleep(0.1)
                        else:
                            print_screen("Errore: Timeout raggiunto senza ricevere l'ACK. Ritrasmissione..\n")
                            retry_count += 1;
                    if(ack_received):
                        break
        except Exception as e:
            print_screen(f"Errore: {e}")
        await asyncio.sleep(8)
        
async def send_ack(lora):
    while(True):
        await lora.transmit_ack(2, bytes.fromhex("DC:54:75:D0:12:28".replace(":", "")))
        await asyncio.sleep(2)
    
async def main_task():
    print_screen("CIAO MONDO")
    
    lora = loraL2.LoRaLevel2Protocol()
    await asyncio.gather(
        asyncio.create_task(send(lora)
        )
    )

if __name__ == "__main__":
    asyncio.run(main_task())