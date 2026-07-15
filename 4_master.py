# 2_master.py
import rpyc
from rpyc.utils.server import ThreadedServer
import time
import sys
import threading

FRUITS = [['pomme', 5], ['banane', 3], ['orange', 10], ['kiwi', 4], ['fraise', 1]]

class MasterService(rpyc.Service):
    lock = threading.Lock()
    results = []
    total_tasks = len(FRUITS)
    server_instance = None  # Permettra d'éteindre le socket proprement
    
    # Base de données d'état partagée entre les connexions
    tasks = [
        {
            "id": idx,
            "fruit": name,
            "temps": temps,
            "status": "PENDING",
            "assigned_to": None,
            "start_time": None
        }
        for idx, (name, temps) in enumerate(FRUITS)
    ]

    def exposed_get_task(self, slave_id: str):
        with self.lock:
            now = time.time()
            
            # 1. Nettoyage des Timeouts (Récupération des tâches perdues)
            for task in self.tasks:
                if task["status"] == "PROCESSING":
                    # Simulation à 0.2s par fruit + 0.8 seconde de marge de tolérance
                    expected_duration = task["temps"] 
                    timeout_limit = expected_duration + 3
                    
                    if now - task["start_time"] > timeout_limit:
                        print(f"\n[Master] TIMEOUT détecté pour {task['assigned_to']} sur '{task['fruit']}' ({task['temps']}).")
                        print(f"[Master] Réassemblage : La tâche '{task['fruit']}' est remise en attente.")
                        task["status"] = "PENDING"
                        task["assigned_to"] = None
                        task["start_time"] = None

            # 2. Recherche d'une tâche PENDING
            for task in self.tasks:
                if task["status"] == "PENDING":
                    task["status"] = "PROCESSING"
                    task["assigned_to"] = slave_id
                    task["start_time"] = now
                    print(f"[Master] Tâche '{task['fruit']}' ({task['temps']}) assignée à {slave_id}")
                    return "PROCESS", (task["id"], task["fruit"], task["temps"])

            # 3. S'il reste des tâches en cours de traitement, on fait patienter l'esclave
            any_processing = any(t["status"] == "PROCESSING" for t in self.tasks)
            if any_processing:
                return "WAIT", None

            # 4. Si tout est fini, signal de déconnexion globale
            return "SHUTDOWN", None

    def exposed_submit_result(self, slave_id: str, task_id: int, result: str):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    # Protection contre les esclaves "revenus d'entre les morts" après timeout
                    if task["status"] == "COMPLETED":
                        print(f"[Master] Résultat ignoré de {slave_id} pour '{task['fruit']}' (déjà traité par un autre).")
                        return
                    
                    task["status"] = "COMPLETED"
                    print(f"[{slave_id}] Travail réceptionné : {result}")
                    self.results.append(result)
                    
                    if len(self.results) == self.total_tasks:
                        print("\n--- Salade de fruits prête ! ---")
                        for res in self.results:
                            print(f" - {res}")
                        print("\nToutes les tâches sont terminées. Arrêt du serveur.")
                        
                        # Arrêt asynchrone pour libérer le port proprement sans bloquer l'appel RPC courant
                        if MasterService.server_instance:
                            threading.Thread(target=MasterService.server_instance.close).start()

if __name__ == "__main__":
    server = ThreadedServer(MasterService, port=18812, protocol_config={"allow_public_attrs": True})
    MasterService.server_instance = server
    print("Master RPyC Tolérant aux pannes initialisé sur le port 18812...")
    server.start()