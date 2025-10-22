import uasyncio as asyncio
import uos, sys
from modules import sysctl

async def handle_command(cmd, args):
    if cmd == "help":
        print("Comandos: ls, cat, rm, reboot, mpython, mkdir, rmdir, echo, mem, gpio")
    elif cmd == "ls":
        try:
            path = args[0] if args else "/"
            print(f"Conteudo de {path}:")
            for f in uos.listdir(path):
                print(f"  {f}")
        except Exception as e:
            print(f"Erro: {e}")
    elif cmd == "cat" and args:
        try:
            with open(args[0], "r") as f:
                print(f.read())
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
    elif cmd == "rm" and args:
        try:
            uos.remove(args[0])
            print(f"Arquivo {args[0]} removido.")
        except Exception as e:
            print(f"Erro ao remover: {e}")
    elif cmd == "mkdir" and args:
        try:
            uos.mkdir(args[0])
            print(f"Diretorio {args[0]} criado.")
        except Exception as e:
            print(f"Erro ao criar diretorio: {e}")
    elif cmd == "rmdir" and args:
        try:
            uos.rmdir(args[0])
            print(f"Diretorio {args[0]} removido.")
        except Exception as e:
            print(f"Erro ao remover diretorio: {e}")
    elif cmd == "echo":
        print(" ".join(args))
    elif cmd == "reboot":
        print("Reiniciando em 3 segundos...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            await asyncio.sleep(1)
        print("Reiniciando...")
        await asyncio.sleep_ms(100)
        import machine
        machine.reset()
    elif cmd == "mpython":
        raise SystemExit
    elif cmd == "pwd":
        print(uos.getcwd())
    elif cmd == "mem":
        import gc
        mem_alloc = gc.mem_alloc()
        mem_free = gc.mem_free()
        print(f"Memoria: {mem_alloc} bytes usados, {mem_free} bytes livres")
    elif cmd == "gpio":
        if len(args) >= 2 and args[0] == "read":
            try:
                from machine import Pin
                pin_num = int(args[1])
                p = Pin(pin_num, Pin.IN)
                value = p.value()
                print(f"Pino {pin_num}: {value}")
            except Exception as e:
                print(f"Erro: {e}")
        elif len(args) >= 3 and args[0] == "write":
            try:
                from machine import Pin
                pin_num = int(args[1])
                value = int(args[2])
                p = Pin(pin_num, Pin.OUT)
                p.value(value)
                print(f"Pino {pin_num} setado para {value}")
            except Exception as e:
                print(f"Erro: {e}")
        else:
            print("Uso: gpio read <pin> ou gpio write <pin> <0|1>")
    elif cmd:
        print(f"Comando desconhecido: {cmd}, Digite help para ver a lista de comandos disponiveis.")

async def run():
    sysctl.log("serial_shell: pronto.")
    s_reader = asyncio.StreamReader(sys.stdin)

    while True:
        print("luis-os> ", end="")
        try:
            res = await s_reader.readline()
            line = res.decode().strip()

            if line:
                parts = line.split()
                command = parts[0]
                arguments = parts[1:]
                await handle_command(command, arguments)

        except Exception as e:
            sysctl.log("serial_shell ex:", e)
            await asyncio.sleep(1)