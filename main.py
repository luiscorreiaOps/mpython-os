import uasyncio as asyncio
from modules import init, sysctl, netmgr, webui, serial_shell

async def start_services():
    print("Inicializando subsistemas...")
    sysctl.init()       
    await netmgr.start()   
    asyncio.create_task(webui.run())
    asyncio.create_task(serial_shell.run())
    print("Serviços iniciados.")

async def watchdog():
    while True:
        print("watchdog: alive")
        await asyncio.sleep(60)

def main():
    try:
        asyncio.run(start_services())
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print("main exception:", e)
        import machine
        machine.reset()

if __name__ == "__main__":
    main()
