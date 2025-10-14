import sys, uasyncio as asyncio
from modules import sysctl, init, netmgr

async def run():
    sysctl.log("serial_shell: ready on REPL/serial")
    import sys
    while True:
        try:
            await asyncio.sleep(1)
        except Exception as e:
            sysctl.log("serial_shell ex:", e)
            await asyncio.sleep(1)

def help():
    print("Comandos disponiveis:")
    print("init.list_files(path='/') -> lista arquivos")
    print("netmgr.save_wifi(ssid, password) -> salva credenciais")
    print("init.reboot() -> reinicia")
