import loraL2
import asyncio
import time

async def recv(lora):
    while(True):
        frame = await lora.receive()
        if frame:
            for key, value in frame.items():
                print(f"{key}{value}")
        print('\n')
        dest_id = frame['Source ID: ']
        sequence_number = frame['Sequence Number: ']
        await lora.transmit_ack(sequence_number, bytes.fromhex(dest_id.replace(":", "")))
        # await lora.transmit("ciao")
        
async def main_task():
    lora = loraL2.LoRaLevel2Protocol()
    await asyncio.gather(
        asyncio.create_task(recv(lora))
    )
    
asyncio.run(main_task())