import uasyncio as asyncio
import uos, sys
from modules import sysctl, cmd_handler

async def handle_command(line):
    output, reboot_flag = cmd_handler.process_command(line)

    if output:
        print(output)

    if reboot_flag:
        print("Reiniciando...")
        await asyncio.sleep(3)
        import machine
        machine.reset()

async def run():
    sysctl.log("serial_shell: pronto.")
    s_reader = asyncio.StreamReader(sys.stdin)

    while True:
        try:
            res = await s_reader.readline()
            line = res.decode().strip()

            if line:
                await handle_command(line)

        except Exception as e:
            sysctl.log("serial_shell ex:", e)
            await asyncio.sleep(1)
