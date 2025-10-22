import network, ujson, time, ubinascii, machine, socket
from modules import sysctl
import uasyncio as asyncio

WIFI_CONF = "/wifi.json"
DISCOVERY_PORT = 12345

ENABLE_DISCOVERY_BEACON = False

BEACON_INTERVAL_S = 60

async def send_discovery_beacon(ip_address):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    broadcast_address = ('255.255.255.255', DISCOVERY_PORT)
    
    message = ujson.dumps({
        "name": "luisos-bemvindo",
        "ip": ip_address
    })
    
    sysctl.log(f"Iniciando envio de beacons a cada {BEACON_INTERVAL_S} segundos.")
    while True:
        try:
            s.sendto(message.encode(), broadcast_address)
        except Exception as e:
            sysctl.log("Erro ao enviar beacon:", e)
        await asyncio.sleep(BEACON_INTERVAL_S)

async def start():
    sysctl.log("netmgr: start")
    
    sta = network.WLAN(network.STA_IF)
    if sta.active():
        sysctl.log("Resetando interface Wifi...")
        sta.disconnect()
        sta.active(False)
        await asyncio.sleep_ms(500)

    try:
        with open(WIFI_CONF, "r") as f:
            cfg = ujson.load(f)
    except Exception:
        cfg = None

    if cfg and cfg.get("ssid"):
        sysctl.log(f"Tentando conectar a rede: '{cfg.get('ssid')}'")
        sta.active(True)
        await asyncio.sleep_ms(200)
        sta.connect(cfg.get("ssid"), cfg.get("password") or "")
        
        for i in range(10):
            sysctl.log(f"Aguardando conexao... ({i+1}/10)")
            if sta.isconnected():
                ip_info = sta.ifconfig()
                ip_address = ip_info[0]
                sysctl.log(f"************ SUCESSO NA CONEXAO ************")
                sysctl.log(f"IP: {ip_address}")
                sysctl.log(f"******************************************")
                
                if ENABLE_DISCOVERY_BEACON:
                    asyncio.create_task(send_discovery_beacon(ip_address))
                else:
                    sysctl.log("Beacon desativado.")

                return
            await asyncio.sleep(1)
        
        sysctl.log("!!!! FALHA NA CONEXAO WIFI !!!!")
        sta.active(False)
    
    sysctl.log("Criando AP fallback...")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ssid = "Luisos-AP"
    ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    sysctl.log(f"AP iniciado'{ssid}'")
    return

def save_wifi(ssid, password=""):
    import ujson
    cfg = {"ssid": ssid, "password": password}
    with open(WIFI_CONF, "w") as f:
        ujson.dump(cfg, f)
    sysctl.log("Wifi salvo:", ssid)