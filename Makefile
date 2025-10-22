PORT ?= /dev/ttyUSB0
FIRMWARE ?= firmware.bin

PYFILES = boot.py main.py set_wifi.py reset.py \
          modules/init.py modules/sysctl.py modules/netmgr.py modules/webui.py \
          modules/serial_shell.py modules/updater.py \
          assets/index.html

MPY_CROSS = mpy-cross

%.mpy: %.py
	$(MPY_CROSS) $<

compile: $(patsubst %.py,%.mpy,$(wildcard modules/*.py))

.PHONY: deploy deploy-full clean ls flash-firmware

deploy:
	@echo "--- Iniciando deploy rapido (arquivos) ---"
	@echo "Verificando conexao com dispositivo..."
	@-mpremote connect $(PORT) ls > /dev/null 2>&1 || { \
		echo "Dispositivo nao responde. Resetando..."; \
		esptool.py --port $(PORT) run > /dev/null 2>&1; \
		sleep 5; \
	}
	@echo "Copiando arquivos..."
	@-mpremote connect $(PORT) fs mkdir /modules 2>/dev/null || true
	@-mpremote connect $(PORT) fs mkdir /assets 2>/dev/null || true
	@for f in $(PYFILES); do \
		echo "Enviando $$f"; \
		mpremote connect $(PORT) fs cp $$f :/$$f 2>/dev/null || { \
			echo "Falha ao enviar $$f, tentando novamente..."; \
			sleep 2; \
			mpremote connect $(PORT) fs cp $$f :/$$f; \
		}; \
	done
	@echo "Enviando config Wifi..."
	@-mpremote connect $(PORT) run set_wifi.py 2>/dev/null || echo "Config wifi enviada (pode ter reiniciado)"
	@echo "\nDEPLOY RAPIDO CONCLUIDO."

deploy-full: flash-firmware
	@echo "\n--- Copiando arquivos para o dispositivo limpo ---"
	@sleep 5
	@-mpremote connect $(PORT) fs mkdir /modules 2>/dev/null || true
	@-mpremote connect $(PORT) fs mkdir /assets 2>/dev/null || true
	@for f in $(PYFILES); do \
		echo "Enviando $$f"; \
		mpremote connect $(PORT) fs cp $$f :/$$f; \
	done
	@echo "\n--- Enviando configuracao de Wifi..."
	@-mpremote connect $(PORT) run set_wifi.py
	@echo "\nDEPLOY COMPLETO. Dispositivo pronto."

flash-firmware:
	@echo "--- LIMPEZA PROFUNDA ---"
	@echo "Apagando flash e reinstalando firmware..."
	@if [ ! -f "$(FIRMWARE)" ]; then echo "ERRO: Arquivo '$(FIRMWARE)' nao encontrado."; exit 1; fi
	esptool.py --chip esp32 --port $(PORT) erase_flash
	esptool.py --chip esp32 --port $(PORT) write_flash -z 0x1000 $(FIRMWARE)
	@echo "Aguardando 5 segundos para inicializacao..."
	@sleep 5

clean:
	@echo "Limpando filesystem..."
	@-mpremote connect $(PORT) reset > /dev/null 2>&1 || true
	@echo "Aguardando 3 segundos..."
	@sleep 3
	@-mpremote connect $(PORT) fs rm -r / 2>/dev/null || true

ls:
	@echo "Listando arquivos na raiz..."
	@-mpremote connect $(PORT) fs ls / 2>/dev/null || echo "Nao foi possivel listar arquivos"

repl:
	@echo "Abrindo REPL..."
	@-mpremote connect $(PORT) repl

reset:
	@echo "Reiniciando dispositivo..."
	@-esptool.py --port $(PORT) run > /dev/null 2>&1

monitor:
	@echo "Monitor serial..."
	@-mpremote connect $(PORT) monitor