import uasyncio as asyncio
from modules import init, sysctl, netmgr, webui, serial_shell

async def start_services():
    print("Inicializando subsistemas...")
    sysctl.init()

    await netmgr.start()

    asyncio.create_task(webui.run())
    asyncio.create_task(serial_shell.run())
    print("Serviços iniciados.")

def main():
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(start_services())
        loop.run_forever()
    except Exception as e:
        print("main exception:", e)
        import machine
        machine.reset()

if __name__ == "__main__":
    main()