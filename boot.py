import machine, ubinascii, uos

#LED config
try:
    led = machine.Pin(2, machine.Pin.OUT)
    led.off()
except Exception:
    led = None

def device_id():
    try:
        uid = ubinascii.hexlify(machine.unique_id()).decode()
        return "mp-esp32-" + uid[-6:]
    except Exception:
        return "mp-esp32-unknown"

DEVICE_ID = device_id()
#uos.mount / vars 
print("Booting", DEVICE_ID)

import time
time.sleep(0.1)
