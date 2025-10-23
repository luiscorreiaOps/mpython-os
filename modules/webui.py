import uasyncio as asyncio
import uos
import ujson
import machine
import gc
import utime
import ubinascii
from modules import sysctl, netmgr

HOST = ""
PORT = 80

# Map MIME 
MIME_TYPES = {
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.html': 'text/html'
}

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
        "Digite 'help' para ver a lista de comandos disponiveis - embreve novos."
    )
    return motd


def get_query_params(path):
    if '?' not in path:
        return {}
    qs = path.split('?', 1)[1]
    params = {}
    for part in qs.split('&'):
        kv = part.split('=', 1)
        if len(kv) == 2:
            params[kv[0]] = kv[1]
    return params


def url_decode(s):
    s = s.replace('%2F', '/').replace('%20', ' ')
    return s


def process_web_command(command_str):
    parts = command_str.split()
    cmd = parts[0] if parts else ""
    args = parts[1:]
    output = ""
    reboot_flag = False
    
    try:
        if cmd == "help": 
            output = "Comandos: ls [path], cat <file>, rm <file>, pwd, mkdir <dir>, rmdir <dir>, echo <text>, mem, gpio, reboot"
        elif cmd == "pwd": 
            output = uos.getcwd()
        elif cmd == "ls":
            path = args[0] if args else "."
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
            output = "Reiniciando em 3 segundos..."
            reboot_flag = True
        elif cmd == "mem":
            mem_alloc = gc.mem_alloc()
            mem_free = gc.mem_free()
            output = f"Memoria: {mem_alloc} bytes usados, {mem_free} bytes livres"
        elif cmd == "gpio":
            if len(args) >= 2 and args[0] == "read":
                try:
                    pin_num = int(args[1])
                    from machine import Pin
                    p = Pin(pin_num, Pin.IN)
                    value = p.value()
                    output = f"Pino {pin_num}: {value}"
                except Exception as e:
                    output = f"Erro: {e}"
            elif len(args) >= 3 and args[0] == "write":
                try:
                    pin_num = int(args[1])
                    value = int(args[2])
                    from machine import Pin
                    p = Pin(pin_num, Pin.OUT)
                    p.value(value)
                    output = f"Pino {pin_num} setado para {value}"
                except Exception as e:
                    output = f"Erro: {e}"
            else:
                output = "Uso: gpio read <pin> ou gpio write <pin> <0|1>"
        elif not cmd: 
            output = ""
        else: 
            output = f"Comando desconhecido: {cmd}"
    except Exception as e: 
        output = f"Erro: {e}"
    
    return output, reboot_flag


def handle_gpio_request(method, pin_str, body_bytes=None):
    try:
        pin_num = int(pin_str)
        if pin_num < 0 or pin_num > 39:
            return '{"error": "Pino invalido (0-39)"}', 400
    except ValueError:
        return '{"error": "Pino deve ser numero"}', 400

    try:
        if method == "GET":
            from machine import Pin, ADC
            p = Pin(pin_num)
            digital_value = p.value()
            analog_value = None
            
            if 32 <= pin_num <= 39:
                try:
                    adc = ADC(Pin(pin_num))
                    adc.atten(ADC.ATTN_11DB)
                    analog_value = adc.read()
                except OSError:
                    analog_value = None

            result = {"pin": pin_num, "digital": digital_value, "analog": analog_value}
            return ujson.dumps(result), 200
            
        elif method == "POST":
            data = ujson.loads(body_bytes.decode())
            mode = data.get("mode", "output")
            value = data.get("value")
            
            if mode == "output":
                from machine import Pin
                p = Pin(pin_num, Pin.OUT)
                p.value(value)
                return '{"status": "OK"}', 200
                
            elif mode == "pwm" and value is not None:
                from machine import PWM
                p = PWM(Pin(pin_num))
                p.freq(1000)
                p.duty(value)
                return '{"status": "OK"}', 200
                
            return '{"error": "Modo invalido"}', 400
                
    except OSError as e:
        return f'{{"error": "{str(e)}"}}', 500
        
    return '{"error": "Metodo nao suportado"}', 405


def is_directory(path):
    try:
        uos.listdir(path)
        return True
    except OSError:
        return False


async def serve_static_file(writer, file_path):
    """Serve arquivos estáticos como CSS, JS, etc."""
    try:
        # MIME base ext
        content_type = 'text/plain'
        for ext, mime_type in MIME_TYPES.items():
            if file_path.endswith(ext):
                content_type = mime_type
                break
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        resp = f"HTTP/1.0 200 OK\r\nContent-Type: {content_type}; charset=utf-8\r\n\r\n{content}"
        await writer.awrite(resp)
        
    except OSError:
        await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")


# API
async def handle_api_request(method, full_path, body_bytes, writer):
    if full_path.startswith("/api/motd"):
        motd_text = get_motd()
        body = ujson.dumps({"motd": motd_text})
        resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
        await writer.awrite(resp)

    elif full_path.startswith("/api/files"):
        params = get_query_params(full_path)
        path = url_decode(params.get("path", ""))
        
        try:
            if path:
                files = uos.listdir(path)
            else:
                files = uos.listdir()
                path = ""
            
            file_list = []
            dir_list = []
            
            for item in files:
                full_item_path = path + "/" + item if path else item
                try:
                    if is_directory(full_item_path):
                        dir_list.append(item)
                    else:
                        file_list.append(item)
                except:
                    file_list.append(item)
            
            dir_list.sort()
            file_list.sort()
            all_files = dir_list + file_list
            
            body = ujson.dumps({"path": path or "/", "files": all_files})
            resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)
        except OSError as e:
            body = ujson.dumps({"error": str(e)})
            resp = "HTTP/1.0 404 NOT FOUND\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)

    elif full_path.startswith("/api/read"):
        params = get_query_params(full_path)
        filename = url_decode(params.get("file", ""))
        if not filename:
            await writer.awrite("HTTP/1.0 400 BAD REQUEST\r\n\r\n")
            return
        chunk_size = 1024  # 1 KB por vez
        
        try:
            resp_header = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n{\"filename\":\"" + filename + "\",\"content\":\""
            await writer.awrite(resp_header)
            
            with open(filename, "r") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    data = data.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
                    await writer.awrite(data)
            
            await writer.awrite("\"}")
        except OSError as e:
            body = ujson.dumps({"error": str(e)})
            resp = "HTTP/1.0 404 NOT FOUND\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)

    elif full_path.startswith("/api/write") and method == "POST":
        data = ujson.loads(body_bytes.decode())
        filename = data.get("filename")
        try:
            with open(filename, "w") as f:
                f.write(data.get("content"))
            resp = "HTTP/1.0 200 OK\r\n\r\n"
            await writer.awrite(resp)
        except OSError as e:
            resp = f"HTTP/1.0 500 ERROR\r\n\r\n{str(e)}"
            await writer.awrite(resp)

    elif full_path.startswith("/api/delete"):
        params = get_query_params(full_path)
        filename = url_decode(params.get("file", ""))
        try:
            if is_directory(filename):
                uos.rmdir(filename)
            else:
                uos.remove(filename)
            resp = "HTTP/1.0 200 OK\r\n\r\n"
            await writer.awrite(resp)
        except OSError as e:
            resp = f"HTTP/1.0 500 ERROR\r\n\r\n{str(e)}"
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
        result, status = handle_gpio_request(method, pin_str, body_bytes)
        resp = f"HTTP/1.0 {status} OK\r\nContent-Type: application/json\r\n\r\n{result}"
        await writer.awrite(resp)
        
    else:
        await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")


#Client
async def handle_client(reader, writer):
    try:
        req_line = await reader.readline()
        if not req_line or req_line == b"\r\n":
            await writer.aclose()
            return

        req_str = req_line.decode('utf-8', 'ignore')
        parts = req_str.split()
        if len(parts) < 2:
            await writer.aclose()
            return
            
        method, full_path, _ = parts
        sysctl.log("HTTP", method, full_path)

        content_len = 0
        headers = {}
        while True:
            header_line = await reader.readline()
            if header_line == b"\r\n":
                break
            header_str = header_line.decode('utf-8', 'ignore').strip()
            if ':' in header_str:
                key, value = header_str.split(':', 1)
                headers[key.strip().lower()] = value.strip()
                if key.strip().lower() == 'content-length':
                    content_len = int(value.strip())
                
        body_bytes = await reader.readexactly(content_len) if content_len > 0 else b''

        #estatico
        if full_path == "/":
            with open('assets/index.html', 'r') as f:
                body = f.read()
            resp = "HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + body
            await writer.awrite(resp)
        elif full_path.startswith("/assets/"):
            file_path = full_path[1:]  # erro barra inicial
            await serve_static_file(writer, file_path)
        else:
            await handle_api_request(method, full_path, body_bytes, writer)

        await writer.aclose()
    except Exception as e:
        sysctl.log("webui handle error:", e)
        try:
            await writer.aclose()
        except OSError:
            pass



async def run():
    sysctl.log("webui iniciou na porta: ", PORT)
    try:
        srv = await asyncio.start_server(handle_client, HOST, PORT)
        await srv.wait_closed()
    except Exception as e:
        sysctl.log("webui error:", e)