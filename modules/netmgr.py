import network, ujson, time, ubinascii, machine
from modules import sysctl
import uasyncio as asyncio

WIFI_CONF = "/wifi.json"

async def start():
    sysctl.log("netmgr: start")
    try:
        with open(WIFI_CONF, "r") as f:
            cfg = ujson.load(f)
    except Exception:
        cfg = None

    if cfg and cfg.get("ssid"):
        sysctl.log("Conectando a rede:", cfg.get("ssid"))
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect(cfg.get("ssid"), cfg.get("password") or "")
        for i in range(20):
            if sta.isconnected():
                sysctl.log("Conectado:", sta.ifconfig())
                return
            await asyncio.sleep(1)
        sysctl.log("Falha na conexão. Criando AP fallback.")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ssid = "mp-esp32-AP"
    ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    sysctl.log("AP iniciado:", ssid)
    return

def save_wifi(ssid, password=""):
    import ujson
    cfg = {"ssid": ssid, "password": password}
    with open(WIFI_CONF, "w") as f:
        ujson.dump(cfg, f)
    sysctl.log("WiFi salvo:", ssid)
