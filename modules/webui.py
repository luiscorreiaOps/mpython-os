import uasyncio as asyncio
import uos
import ujson
import machine
import gc
import utime
import ubinascii
from modules import sysctl, netmgr, cmd_handler, cron

HOST = ""
PORT = 80

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
        f"Bem-vindo ao LuisOS v0.2 ({sys_info.release})\n"
        f"------------------------------------\n"
        f"* DEVICE ID:  {device_id[-6:]}\n"
        f"* PLATFORM:   {sys_info.machine}\n"
        f"* MEMORY:     {mem_alloc:.2f} KB / {mem_total:.2f} KB utilizados\n"
        f"* UPTIME:     {days}d {hours}h {minutes}m\n\n"
        "Digite 'help' para ver a lista de comandos\ndisponiveis."
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

def url_decode(s):
    return s.replace('%2F', '/').replace('%20', ' ').replace('%2E', '.')

async def serve_static_file(writer, file_path):
    try:
        ctype = 'text/plain'
        for ext, m in MIME_TYPES.items():
            if file_path.endswith(ext): ctype = m; break
        with open(file_path, 'r') as f:
            content = f.read()
        resp = f"HTTP/1.0 200 OK\r\nContent-Type: {ctype}\r\n\r\n{content}"
        await writer.awrite(resp)
    except:
        await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")

async def handle_api_request(method, full_path, body_bytes, writer):
    if full_path.startswith("/api/motd"):
        body = ujson.dumps({"motd": get_motd()})
        await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body)

    elif full_path.startswith("/api/files"):
        params = get_query_params(full_path)
        path = url_decode(params.get("path", ""))
        try:
            files = uos.listdir(path) if path else uos.listdir()
            body = ujson.dumps({"path": path or "/", "files": sorted(files)})
            await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body)
        except: await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")

    elif full_path.startswith("/api/read"):
        params = get_query_params(full_path)
        fname = url_decode(params.get("file", ""))
        try:
            with open(fname, "r") as f: content = f.read()
            body = ujson.dumps({"filename": fname, "content": content})
            await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body)
        except: await writer.awrite("HTTP/1.0 404 NOT FOUND\r\n\r\n")

    elif full_path.startswith("/api/write"):
        try:
            data = ujson.loads(body_bytes.decode())
            with open(data["filename"], "w") as f: f.write(data["content"])
            await writer.awrite("HTTP/1.0 200 OK\r\n\r\n{\"status\":\"ok\"}")
        except: await writer.awrite("HTTP/1.0 500 ERROR\r\n\r\n")

    elif full_path.startswith("/api/delete"):
        params = get_query_params(full_path)
        fname = url_decode(params.get("file", ""))
        try:
            try:
                uos.listdir(fname)
                uos.rmdir(fname)
            except OSError:
                uos.remove(fname)
            await writer.awrite("HTTP/1.0 200 OK\r\n\r\n")
        except: await writer.awrite("HTTP/1.0 500 ERROR\r\n\r\n")

    elif full_path.startswith("/api/exec"):
        try:
            cmd_data = ujson.loads(body_bytes.decode())
            out, reb = cmd_handler.process_command(cmd_data.get("command", ""))
            await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + ujson.dumps({"output":out}))
            if reb:
                async def d_reb(): await asyncio.sleep(2); machine.reset()
                asyncio.create_task(d_reb())
        except: await writer.awrite("HTTP/1.0 500 ERROR\r\n\r\n")

    elif full_path.startswith("/api/cron/list"):
        body = ujson.dumps({"tasks": cron.scheduler.tasks})
        await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body)

    elif full_path.startswith("/api/cron/add"):
        data = ujson.loads(body_bytes.decode())
        cron.scheduler.add_task(data.get("interval"), data.get("command"))
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n")

    elif full_path.startswith("/api/cron/delete"):
        params = get_query_params(full_path)
        cron.scheduler.remove_task(params.get("id", ""))
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n")

    elif full_path.startswith("/api/wifi/status"):
        import network
        sta, ap = network.WLAN(network.STA_IF), network.WLAN(network.AP_IF)
        status = {"mode": "Desconectado", "ssid": ""}
        if sta.isconnected(): status = {"mode": "STA", "ssid": sta.config("ssid")}
        elif ap.active(): status = {"mode": "AP", "ssid": ap.config("essid")}
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n" + ujson.dumps(status))

    elif full_path.startswith("/api/setwifi"):
        data = ujson.loads(body_bytes.decode())
        netmgr.save_wifi(data.get("ssid"), data.get("password"))
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n")
        async def d_reb(): await asyncio.sleep(1); machine.reset()
        asyncio.create_task(d_reb())

    elif full_path.startswith("/api/gpio/"):
        pin_str = full_path.split('/')[3]
        from machine import Pin, ADC
        p_num = int(pin_str)
        val = 0
        if 32 <= p_num <= 39:
            adc = ADC(Pin(p_num)); adc.atten(ADC.ATTN_11DB); val = adc.read()
        else: val = Pin(p_num).value() * 4095
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n" + ujson.dumps({"analog": val}))

async def handle_upload(reader, writer, full_path, clen):
    params = get_query_params(full_path)
    fname = url_decode(params.get("file", "upload.bin"))
    try:
        with open(fname, "wb") as f:
            remain = clen
            while remain > 0:
                chunk = await reader.readexactly(min(remain, 1024))
                f.write(chunk)
                remain -= len(chunk)
        await writer.awrite("HTTP/1.0 200 OK\r\n\r\n{\"status\":\"ok\"}")
    except Exception as e:
        await writer.awrite("HTTP/1.0 500 ERROR\r\n\r\n" + str(e))

async def handle_client(reader, writer):
    try:
        line = await reader.readline()
        if not line or line == b"\r\n": return
        parts = line.decode().split()
        if len(parts) < 2: return
        method, path = parts[0], parts[1]
        clen = 0
        while True:
            h = await reader.readline()
            if h == b"\r\n": break
            if h.lower().startswith(b"content-length:"): clen = int(h.split(b":")[1])

        if path.startswith("/api/upload") and method == "POST":
            await handle_upload(reader, writer, path, clen)
        else:
            body = await reader.readexactly(clen) if clen > 0 else b''
            if path == "/":
                with open('assets/index.html', 'r') as f: c = f.read()
                await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n" + c)
            elif path.startswith("/assets/"):
                await serve_static_file(writer, path[1:])
            else:
                await handle_api_request(method, path, body, writer)
        await writer.aclose()
    except Exception as e:
        sysctl.log("WebError:", e)
        try: await writer.aclose()
        except: pass

async def run():
    sysctl.log("WebUI porta", PORT)
    await asyncio.start_server(handle_client, "0.0.0.0", PORT)
