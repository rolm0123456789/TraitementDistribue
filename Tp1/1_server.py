# server_rpyc.py
import rpyc
from rpyc.utils.server import ThreadedServer

class AnswerService(rpyc.Service):
    def exposed_get_value(self):
        return 42

if __name__ == "__main__":
    # RPyC utilise par défaut le port 18812
    server = ThreadedServer(AnswerService, port=18812)
    print("Serveur RPyC démarré sur le port 18812...")
    server.start()