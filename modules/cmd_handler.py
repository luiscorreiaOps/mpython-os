import uos
import gc
import machine
from modules import sysctl

def process_command(command_str):
    parts = command_str.split()
    cmd = parts[0] if parts else ""
    args = parts[1:]
    output = ""
    reboot_flag = False
    
    try:
        if cmd == "help": 
            output = "Comandos: ls [path], cd, touch, cat, rm, pwd,\nmkdir, rmdir, echo, clear, mem, gpio, reboot."
        elif cmd == "pwd": 
            output = uos.getcwd()
        elif cmd == "cd":
            path = args[0] if args else "/"
            uos.chdir(path)
            output = "Diretorio alterado para: " + uos.getcwd()
        elif cmd == "touch" and args:
            with open(args[0], "a"):
                pass
            output = "Arquivo criado: " + args[0]
        elif cmd == "ls":
            path = args[0] if args else "."
            files = uos.listdir(path)
            output = "Conteudo: " + ", ".join(files)
        elif cmd == "cat" and args:
            with open(args[0], "r") as f: 
                output = f.read()
        elif cmd == "rm" and args:
            uos.remove(args[0])
            output = "Removido: " + args[0]
        elif cmd == "mkdir" and args:
            uos.mkdir(args[0])
            output = "Criado: " + args[0]
        elif cmd == "rmdir" and args:
            uos.rmdir(args[0])
            output = "Removido: " + args[0]
        elif cmd == "echo":
            output = " ".join(args)
        elif cmd == "reboot":
            output = "Reiniciando..."
            reboot_flag = True
        elif cmd == "mem":
            output = "RAM: " + str(gc.mem_free()) + " bytes livres"
        elif cmd == "gpio":
            if len(args) >= 2 and args[0] == "read":
                p = machine.Pin(int(args[1]), machine.Pin.IN)
                output = "Pino " + args[1] + ": " + str(p.value())
            elif len(args) >= 3 and args[0] == "write":
                p = machine.Pin(int(args[1]), machine.Pin.OUT)
                p.value(int(args[2]))
                output = "Pino " + args[1] + " setado para " + args[2]
            else:
                output = "Uso: gpio read <pin> ou gpio write <pin> <0|1>"
        elif not cmd: 
            output = ""
        else: 
            output = "Comando desconhecido: " + cmd
    except Exception as e: 
        output = "Erro: " + str(e)
    
    return output, reboot_flag
