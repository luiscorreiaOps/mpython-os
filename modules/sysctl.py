import machine, sys

led = None

def init():
    global led
    try:
        led = machine.Pin(2, machine.Pin.OUT)
        led.off()
    except Exception:
        led = None

def led_on():
    if led:
        led.on()

def led_off():
    if led:
        led.off()

def log(*args, **kwargs):
    print("[SYS]", *args)
