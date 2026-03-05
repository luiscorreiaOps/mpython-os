import uos
import machine
from modules import netmgr

netmgr.save_wifi("<NOMEUID>", "<PASSUUID>")

try:
    uos.remove('/deploy.lock')
    print("Trava de deploy removido.")
except OSError:
    pass

machine.reset()
