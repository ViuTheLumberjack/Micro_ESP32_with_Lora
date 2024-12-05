from txrxlora import get_modem
from loraL2 import transmit, receive

import time

def main():
    counter = 0
    message = f"{counter!r} from lora MLFDS"
    while True:
        transmit(message)
        time.sleep(2)
        counter += 1

if __name__ == "__main__":
    main()