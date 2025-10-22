import socket, uasyncio as asyncio, ure, sys, uos, ujson, machine, gc, utime, ubinascii
from modules import sysctl, netmgr

HOST = ""
PORT = 80

def get_motd():
    sys_info = uos.uname()
    device_id = ubinascii.hexlify(machine.unique_id()).decode()
    
    mem_alloc = gc.mem_alloc() / 1024
    mem_free = gc.mem_free() / 1024
    mem_total = mem_alloc + mem_free
    uptime_s = utime.ticks_ms() // 1000
    days = uptime_s // 86400
    hours = (uptime_s % 86400) // 3600
    minutes = (uptime_s % 3600) // 60
    
    motd = (
        f"Bem-vindo ao LuisOS v0.1 ( {sys_info.release})\n"
        f"---------------------------------------------------\n"
        f"* DEVICE ID:  {device_id[-6:]}\n"
        f"* PLATFORM:   {sys_info.machine}\n"
        f"* MEMORY:     {mem_alloc:.2f} KB / {mem_total:.2f} KB utilizados\n"
        f"* UPTIME:     {days}d {hours}h {minutes}m\n\n"
        "Digite 'help' para ver a lista de comandos disponiveis - Embreve novos!"
    )
    return motd

def get_query_params(path):
    if '?' not in path: return {}
    qs = path.split('?', 1)[1]
    params = {}
    for part in qs.split('&'):
        kv = part.split('=', 1)
        if len(kv) == 2: params[kv[0]] = kv[1]
    return params

def process_web_command(command_str):
    parts = command_str.split()
    cmd = parts[0] if parts else ""
    args = parts[1:]
    output = ""
    reboot_flag = False
    try:
        if cmd == "help": 
            output = "Comandos: ls [path], cat <file>, rm <file>, pwd, mkdir <dir>, rmdir <dir>, echo <text>,mem, reboot"
        elif cmd == "pwd": 
            output = uos.getcwd()
        elif cmd == "ls":
            path = args[0] if args else uos.getcwd()
            files = uos.listdir(path)
            output = f"Conteudo de {path}:\n" + "\n".join([f"  {f}" for f in files])
        elif cmd == "cat" and args:
            with open(args[0], "r") as f: 
                output = f.read()
        elif cmd == "rm" and args:
            uos.remove(args[0])
            output = f"Arquivo {args[0]} removido."
        elif cmd == "mkdir" and args:
            uos.mkdir(args[0])
            output = f"Diretorio {args[0]} criado."
        elif cmd == "rmdir" and args:
            uos.rmdir(args[0])
            output = f"Diretorio {args[0]} removido."
        elif cmd == "echo":
            output = " ".join(args)
        elif cmd == "reboot":
            output = "O sistema ira reiniciar em 3 segundos..."
            reboot_flag = True
        elif cmd == "mem":
            import gc
            mem_alloc = gc.mem_alloc()
            mem_free = gc.mem_free()
            output = f"Memoria: {mem_alloc} bytes usados, {mem_free} bytes livres"
        elif not cmd: 
            output = ""
        else: 
            output = f"Comando desconhecido: {cmd}"
    except Exception as e: 
        output = f"Erro: {e}"
    return output, reboot_flag

async def handle_client(reader, writer):
    try:
        req_line = await reader.readline()
        if not req_line or req_line == b"\r\n":
            await writer.aclose()
            return

        req_str = req_line.decode('utf-8', 'ignore')
        method, full_path, version = req_str.split()
        sysctl.log("HTTP", method, full_path)

        content_len = 0
        while True:
            header_line = await reader.readline()
            if header_line == b"\r\n": break
            if header_line.lower().startswith(b'content-length:'):
                content_len = int(header_line.split(b':')[1].strip())
        body_bytes = await reader.readexactly(content_len) if content_len > 0 else b''

        if full_path == "/":
            with open('/assets/index.html', 'r') as f: body = f.read()
            resp = "HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + body
            await writer.awrite(resp)
        elif full_path.startswith("/api/motd"):
            motd_text = get_motd()
            body = ujson.dumps({"motd": motd_text})
            resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)
        elif full_path.startswith("/api/files"):
            path = uos.getcwd()
            files = uos.listdir(path)
            body = ujson.dumps({"path": path, "files": files})
            resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)
        elif full_path.startswith("/api/read"):
            params = get_query_params(full_path)
            filename = params.get("file")
            try:
                with open(filename, "r") as f: content = f.read()
                body = ujson.dumps({"filename": filename, "content": content})
                resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
                await writer.awrite(resp)
            except Exception as e:
                body = ujson.dumps({"error": str(e)})
                resp = "HTTP/1.0 404 NOT FOUND\r\nContent-Type: application/json\r\n\r\n" + body
                await writer.awrite(resp)
        elif full_path.startswith("/api/delete"):
            params = get_query_params(full_path)
            filename = params.get("file")
            try:
                uos.remove(filename)
                resp = "HTTP/1.0 200 OK\r\n\r\n"
                await writer.awrite(resp)
            except Exception as e:
                resp = "HTTP/1.0 500 ERROR\r\n\r\n" + str(e)
                await writer.awrite(resp)
        elif full_path.startswith("/api/write") and method == "POST":
            data = ujson.loads(body_bytes.decode())
            try:
                with open(data.get("filename"), "w") as f: f.write(data.get("content"))
                resp = "HTTP/1.0 200 OK\r\n\r\n"
                await writer.awrite(resp)
            except Exception as e:
                resp = "HTTP/1.0 500 ERROR\r\n\r\n" + str(e)
                await writer.awrite(resp)
        elif full_path.startswith("/api/exec") and method == "POST":
            command_data = ujson.loads(body_bytes.decode())
            output_data, reboot_flag = process_web_command(command_data.get("command", ""))
            body = ujson.dumps({"output": output_data})
            resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)
            if reboot_flag:
                async def delayed_reboot():
                    await asyncio.sleep(3)
                    machine.reset()
                asyncio.create_task(delayed_reboot())
        elif full_path.startswith("/api/setwifi") and method == "POST":
            data = ujson.loads(body_bytes.decode())
            ssid = data.get("ssid")
            password = data.get("password")
            if ssid:
                netmgr.save_wifi(ssid, password)
                resp = "HTTP/1.0 200 OK\r\n\r\n"
                await writer.awrite(resp)
                
                async def delayed_reboot():
                    await asyncio.sleep(1)
                    machine.reset()
                asyncio.create_task(delayed_reboot())
            else:
                resp = "HTTP/1.0 400 BAD REQUEST\r\n\r\n"
                await writer.awrite(resp)
        elif full_path.startswith("/api/gpio/") and method in ["GET", "POST"]:
            pin_str = full_path.split('/')[3]
            try:
                pin_num = int(pin_str)
            except ValueError:
                resp = "HTTP/1.0 400 BAD REQUEST\r\n\r\n"
                await writer.awrite(resp)
                await writer.aclose()
                return

            if method == "GET":
                from machine import Pin, ADC
                p = Pin(pin_num)
                digital_value = p.value()
                analog_value = None
                if pin_num >= 32 and pin_num <= 39:
                    try:
                        adc = ADC(Pin(pin_num))
                        adc.atten(ADC.ATTN_11DB)
                        analog_value = adc.read()
                    except Exception:
                        analog_value = None

                body = ujson.dumps({"pin": pin_num, "digital": digital_value, "analog": analog_value})
                resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
                await writer.awrite(resp)

            elif method == "POST":
                data = ujson.loads(body_bytes.decode())
                mode = data.get("mode", "output")
                value = data.get("value")
                from machine import Pin, PWM
                
                if mode == "output":
                    p = Pin(pin_num, Pin.OUT)
                    p.value(value)
                    resp = "HTTP/1.0 200 OK\r\n\r\n"
                elif mode == "pwm":
                    p = PWM(Pin(pin_num))
                    p.freq(1000)
                    p.duty(value)
                    resp = "HTTP/1.0 200 OK\r\n\r\n"
                else:
                    resp = "HTTP/1.0 400 BAD REQUEST\r\n\r\n"
                await writer.awrite(resp)
        else:
            await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")

        await writer.aclose()
    except Exception as e:
        sysctl.log("webui handle error:", e)
        try:
            await writer.aclose()
        except:
            pass

async def run():
    sysctl.log("webui iniciou na porta: ", PORT)
    try:
        srv = await asyncio.start_server(handle_client, HOST, PORT)
        await srv.wait_closed()
    except Exception as e:
        sysctl.log("webui error:", e)