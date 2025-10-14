import uos, machine, utime

def uptime():
    return utime.ticks_ms()

def reboot():
    machine.reset()

def list_files(path="/"):
    try:
        return uos.listdir(path)
    except Exception as e:
        return []
