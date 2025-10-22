import machine, ubinascii, uos, time

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
print("Booting", DEVICE_ID)

try:
    uos.stat('/deploy.lock')
    print("Modo de deploy detectado. Pulando inicializacao.")
except OSError:
    print("Inicializacao normal...")
    import main

time.sleep(0.1)