# servidor.py
from rpyc.utils.server import ThreadedServer
from controller.servidor_controller import JogoService

if __name__ == "__main__":
    server = ThreadedServer(JogoService, port=18812)
    print("Servidor RPyC rodando na porta 18812...")
    server.start()
