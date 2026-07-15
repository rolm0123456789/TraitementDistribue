# master.py
import rpyc
from rpyc.utils.server import ThreadedServer
import queue
import sys

FRUITS = [['pomme', 5], ['banane', 3], ['orange', 10], ['kiwi', 4], ['fraise', 2]]

class MasterService(rpyc.Service):
    # Variables de classe partagées entre toutes les connexions clients
    task_queue = queue.Queue()
    results = []
    total_tasks = len(FRUITS)

    # Remplissage initial de la file d'attente
    for fruit in FRUITS:
        task_queue.put(fruit)

    def exposed_get_task(self):
        """Permet à un esclave de récupérer un fruit à découper."""
        try:
            return self.task_queue.get_nowait()
        except queue.Empty:
            return None  # Plus de travail disponible

    def exposed_submit_result(self, slave_id: str, result: str):
        """Permet à un esclave de soumettre son travail terminé."""
        print(f"[{slave_id}] Travail réceptionné : {result}")
        self.results.append(result)
        
        # Validation de la fin de la préparation
        if len(self.results) == self.total_tasks:
            print("\n--- Salade de fruits prête ! ---")
            for preparation in self.results:
                print(f" - {preparation}")
            print("\nToutes les tâches sont terminées. Arrêt du serveur.")
            sys.exit(0)

if __name__ == "__main__":
    # Le Master écoute sur un port unique
    server = ThreadedServer(MasterService, port=18812)
    print("Master RPyC en attente d'esclaves sur le port 18812...")
    server.start()