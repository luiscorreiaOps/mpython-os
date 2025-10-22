from modules import netmgr
import uos

netmgr.save_wifi("SIID", "PSS")

try:
    uos.remove('/deploy.lock')
    print("Trava de deploy removido.")
except OSError:
    pass

import machine
machine.reset()