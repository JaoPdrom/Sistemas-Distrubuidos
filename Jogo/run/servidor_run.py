# servidor_run.py

import sys
import os
import socket
from rpyc.utils.server import ThreadedServer
from controller.servidor_controller import JogoService # Importação corrigida

# Adiciona o diretório raiz ao path para garantir que 'service' seja encontrado
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

hostname = socket.gethostname()
endereco_ip = socket.gethostbyname(hostname)
porta = 18812

print("Iniciando Servidor RPyC...")
print(f"Endereço: {endereco_ip}")
print(f"Porta {porta} ")

#instancia o servidor
t = ThreadedServer(JogoService, port=porta)

#inicia o servidor
t.start()