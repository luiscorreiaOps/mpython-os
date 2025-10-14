PORT ?= /dev/ttyUSB0
BAUD ?= 115200

PYFILES = boot.py main.py set_wifi.py modules/init.py modules/sysctl.py modules/netmgr.py modules/webui.py modules/serial_shell.py modules/updater.py assets/index.html

.PHONY: flash-firmware deploy clean ls


flash-firmware:
	@if [ -z "$(FIRMWARE)" ]; then echo "Defina FIRMWARE=path/to/firmware.bin"; exit 1; fi
	esptool.py --chip esp32 --port $(PORT) --baud 460800 erase_flash
	esptool.py --chip esp32 --port $(PORT) --baud 460800 write_flash -z 0x1000 $(FIRMWARE)

deploy:
	@echo "Criando pastas necessárias no dispositivo..."
	mpremote connect $(PORT) fs mkdir /modules || true
	mpremote connect $(PORT) fs mkdir /assets || true
	@echo "Copiando arquivos..."
	for f in $(PYFILES); do \
		mpremote connect $(PORT) fs cp $$f :/$$f; \
	done
	@echo "Criando reset.py temporário..."
	@echo "import machine" > reset.py
	@echo "machine.reset()" >> reset.py
	mpremote connect $(PORT) fs cp reset.py :/reset.py
	@echo "Reiniciando dispositivo..."
	mpremote connect $(PORT) run reset.py
	@rm -f reset.py

#filesystem
clean:
	mpremote connect $(PORT) fs rm -r /

ls:
	mpremote connect $(PORT) fs ls /