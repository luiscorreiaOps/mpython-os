import serial.tools.list_ports
import sys

def find_esp32_ports():
    esp32_ports = []
    
    esp32_vid_pids = [
        (0x303A, 0x1001),
        (0x303A, 0x00C3), 
        (0x10C4, 0xEA60),
        (0x1A86, 0x7523),
        (0x0403, 0x6001),
    ]
    
    print("Procurando ESP32...")
    
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("Nenhuma porta serial encontrada")
        return []
    
    for port in ports:
        print(f"Porta: {port.device}")
        print(f"Descricao: {port.description}")
        
        for vid, pid in esp32_vid_pids:
            if f"{vid:04X}:{pid:04X}" in port.hwid.upper():
                esp32_ports.append(port.device)
                print("ESP32 detectado")
                break
        else:
            esp_keywords = ['esp32', 'esp8266', 'cp210', 'ch340', 'ftdi']
            if any(keyword in port.description.lower() for keyword in esp_keywords):
                esp32_ports.append(port.device)
                print("Possivel ESP32")
            else:
                print("Dispositivo desconhecido")
        
        print()
    
    return esp32_ports

def main():
    ports = find_esp32_ports()
    
    if ports:
        print("Portas ESP32 encontradas:")
        for port in ports:
            print(f"  {port}")
    else:
        print("Nenhum ESP32 encontrado")
        print("Tente:")
        print("Em sudoer")
        print("  ls /dev/ttyUSB*")
        print("  ls /dev/ttyACM*")

if __name__ == "__main__":
    main()