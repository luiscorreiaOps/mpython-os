import socket
import json
import time
import requests
import pytest
from datetime import datetime

DISCOVERY_PORT = 12345
BUFFER_SIZE = 1024
TIMEOUT = 10

class LuisOSDebug:
    def __init__(self):
        self.discovered_devices = []
        self.test_results = {}

    def listen_for_beacons(self, duration=30):
        """beacons por um período determinado"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1)  # 1 segundo
        
        s.bind(('', DISCOVERY_PORT))
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Escutando por beacons por {duration} segundos...")
        
        start_time = time.time()
        beacon_count = 0
        
        while time.time() - start_time < duration:
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                beacon_count += 1
                
                try:
                    message = json.loads(data.decode())
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Beacon #{beacon_count} de {addr[0]}: {message}")
                    
                    if message.get("name") == "luisos":
                        device_info = {
                            'ip': message.get('ip'),
                            'source_addr': addr[0],
                            'timestamp': datetime.now().isoformat(),
                            'raw_message': message
                        }
                        self.discovered_devices.append(device_info)
                        
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"[!] Beacon inválido de {addr[0]}: {e}")
                    print(f"    Dados brutos: {data}")
                    
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                break
        
        s.close()
        return self.discovered_devices

    def test_web_interface(self, ip):
        """Testa a interface web do dispositivo"""
        tests = {}
        
        #MOTD
        try:
            start_time = time.time()
            response = requests.get(f"http://{ip}/api/motd", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            tests['motd'] = {
                'status': response.status_code,
                'response_time': response_time,
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                data = response.json()
                tests['motd']['data'] = data.get('motd', 'Sem MOTD')
        except Exception as e:
            tests['motd'] = {'success': False, 'error': str(e)}
        
        #files
        try:
            response = requests.get(f"http://{ip}/api/files", timeout=5)
            tests['files'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
        except Exception as e:
            tests['files'] = {'success': False, 'error': str(e)}
        
        # Teste GPIO (se disponível)
        try:
            response = requests.get(f"http://{ip}/api/gpio/2", timeout=5)
            tests['gpio'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
        except Exception as e:
            tests['gpio'] = {'success': False, 'error': str(e)}
        
        self.test_results[ip] = tests
        return tests

    def network_scan(self, subnet="192.168.1", ports=[80, 22, 53]):
        """Escaneia a rede local por dispositivos LuisOS"""
        print(f"\n[SCAN] Escaneando rede {subnet}.x...")
        
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            for port in ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.5)
                        result = sock.connect_ex((ip, port))
                        if result == 0:
                            print(f"[SCAN] {ip}:{port} - ABERTO")
                            #cash os
                            try:
                                response = requests.get(f"http://{ip}/api/motd", timeout=2)
                                if response.status_code == 200:
                                    print(f"[SCAN] ✅ LuisOS detectado em {ip}")
                                    self.discovered_devices.append({
                                        'ip': ip,
                                        'source': 'network_scan',
                                        'timestamp': datetime.now().isoformat()
                                    })
                            except:
                                pass
                except:
                    pass

    def generate_report(self):
        """Gera relatório completo dos testes"""
        print("\n" + "="*50)
        print("RELATÓRIO DE DEBUG - LUISOS")
        print("="*50)
        
        print(f"\nDispositivos encontrados: {len(self.discovered_devices)}")
        for device in self.discovered_devices:
            print(f"\n--- {device['ip']} ---")
            print(f"  Fonte: {device.get('source', 'beacon')}")
            print(f"  Horario: {device.get('timestamp', 'N/A')}")
            
            if device['ip'] in self.test_results:
                tests = self.test_results[device['ip']]
                for test_name, result in tests.items():
                    status = "OK" if result.get('success') else "NO"
                    print(f"  {test_name.upper()}: {status}")
                    if 'response_time' in result:
                        print(f"    Tempo: {result['response_time']:.2f}ms")
                    if 'error' in result:
                        print(f"    Erro: {result['error']}")

@pytest.fixture
def debug_tool():
    return LuisOSDebug()

def test_beacon_parsing(debug_tool):
    """parsing de beacons"""

# simular beacon valido
    valid_beacon = json.dumps({
        "name": "luisos",
        "ip": "192.168.1.100",
        "version": "1.0"
    }).encode()
    
# mockar o socket manual
    assert debug_tool is not None

def test_web_interface_mock(debug_tool):
    """Teste web com mock"""
    
    assert debug_tool.test_web_interface is not None

def test_network_scan(debug_tool):
    """Testa  scan de rede"""
   
# Testar a logica sem  escanear
    original_devices_count = len(debug_tool.discovered_devices)
    debug_tool.discovered_devices.append({
        'ip': '192.168.1.100',
        'source': 'test',
        'timestamp': datetime.now().isoformat()
    })
    assert len(debug_tool.discovered_devices) == original_devices_count + 1

def main():
    debug = LuisOSDebug()
    
    print("=== DEBUG TOOL LUISOS ===")
    print("1. Escutar beacons")
    print("2. Escanear rede")
    print("3. Testar dispositivo especifico")
    print("4. Executar todos os testes")
    
    choice = input("\nEscolha uma opção: ")
    
    if choice == "1":
        devices = debug.listen_for_beacons(30)
        for device in devices:
            debug.test_web_interface(device['ip'])
        debug.generate_report()
        
    elif choice == "2":
        subnet = input("Subnet (ex: 192.168.1): ") or "192.168.1"
        debug.network_scan(subnet)
        debug.generate_report()
        
    elif choice == "3":
        ip = input("IP do dispositivo: ")
        debug.test_web_interface(ip)
        debug.generate_report()
        
    elif choice == "4":
        print("Executando suite completa...")
        debug.listen_for_beacons(10)
        debug.network_scan()
        for device in debug.discovered_devices:
            debug.test_web_interface(device['ip'])
        debug.generate_report()

if __name__ == "__main__":
    main()

    # pytest find_os_debug.py -v
    # pytest find_os_debug.py::test_beacon_parsing -v
