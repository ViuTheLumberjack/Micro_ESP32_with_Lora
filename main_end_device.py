import loraL2
import asyncio
import time
import machine
import random
    
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
                    await lora.transmit(message)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        ack = await lora.receive()
                        if(ack):
                            if(ack['Type: '] != 'ACK' or ack['Destination ID: '] != MAC or ack['Sequence Number: '] != lora.get_sequence_number()):
                                print("Messaggio ignorato\n")
                            else:
                                print("ACK ricevuto!\n")
                                ack_received = True
                                break
                            await asyncio.sleep(0.1)
                        else:
                            print("Errore: Timeout raggiunto senza ricevere l'ACK. Ritrasmissione..\n")
                            retry_count += 1;
                    if(ack_received):
                        break
        except Exception as e:
            print(f"Errore: {e}")
        await asyncio.sleep(8)
        
async def send_ack(lora):
    while(True):
        await lora.transmit_ack(2, bytes.fromhex("DC:54:75:D0:12:28".replace(":", "")))
        await asyncio.sleep(2)
        
async def main_task():
    lora = loraL2.LoRaLevel2Protocol()
    await asyncio.gather(
        asyncio.create_task(send(lora))
    )

asyncio.run(main_task())