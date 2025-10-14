import socket, uasyncio as asyncio, ure, sys
from modules import sysctl

HOST = ""  #anyint
PORT = 80

async def handle_client(reader, writer):
    try:
        req = await reader.read(1024)
        if not req:
            await writer.aclose()
            return
        req = req.decode('utf-8', 'ignore')

        first_line = req.split("\r\n")[0]
        parts = first_line.split()
        path = parts[1] if len(parts) > 1 else "/"
        sysctl.log("HTTP", path)
        if path == "/":
            body = open('/assets/index.html').read()
            resp = "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n" + body
            await writer.awrite(resp)
        elif path.startswith("/files"):
            import uos, ujson
            files = uos.listdir("/")
            body = ujson.dumps(files)
            resp = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
            await writer.awrite(resp)
        elif path.startswith("/update") and req.find("multipart/form-data") != -1:
            #separador e payload
            try:
                parts = req.split("\r\n\r\n", 1)
                payload = parts[1]
                with open("/uploaded.bin", "wb") as f:
                    f.write(payload.encode('utf-8'))
                await writer.awrite("HTTP/1.0 200 OK\r\n\r\nUpload salvo")
            except Exception as e:
                await writer.awrite("HTTP/1.0 500 ERROR\r\n\r\n" + str(e))
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
    sysctl.log("webui starting on port", PORT)
    try:
        srv = await asyncio.start_server(handle_client, HOST, PORT)
        await srv.wait_closed()
    except Exception as e:
        sysctl.log("webui error:", e)
