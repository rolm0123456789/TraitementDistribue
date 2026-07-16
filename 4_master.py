# 4_master.py (Exercice 4 - Master Résilient)
import rpyc
from rpyc.utils.server import ThreadedServer
import os
import sys
import threading
import time

FRUITS = [['pomme', 5], ['banane', 3], ['orange', 10], ['kiwi', 4], ['fraise', 1]]

class MasterService(rpyc.Service):
    lock = threading.Lock()
    results = []
    events = []  # Historique des pannes et événements en temps réel
    total_tasks = len(FRUITS)
    server_instance = None  # Référence pour éteindre le socket proprement
    
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

    @classmethod
    def _print_dashboard(cls):
        """Efface l'écran et redessine le tableau de bord complet de la V2."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("\n\033[1mSYSTÈME MASTER-SLAVE V2 : TOLÉRANCE AUX PANNES EN TEMPS RÉEL\033[0m\n")
        
        # En-tête du tableau (Largeur optimisée)
        divider = "+" + "-"*15 + "+" + "-"*12 + "+" + "-"*22 + "+" + "-"*12 + "+" + "-"*32 + "+"
        print(divider)
        print("| {:<13} | {:<10} | {:<20} | {:<10} | {:<30} |".format("Fruit", "Temps (s)", "Statut", "Slave ID", "Détails / Résultat"))
        print(divider)
        
        completed_count = 0
        for task in cls.tasks:
            fruit = task["fruit"]
            temps = task["temps"]
            status = task["status"]
            worker = task["assigned_to"] if task["assigned_to"] else "-"
            
            # Formatage dynamique avec gestion des couleurs ANSI
            if status == "PENDING":
                raw_text = "En attente"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[94m{raw_text}...\033[0m") # Bleu
                details = "-"
            elif status == "PROCESSING":
                raw_text = "En cours"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[93m{raw_text}\033[0m") # Jaune
                details = "Découpe active"
            elif status == "COMPLETED":
                completed_count = len(cls.results) # Utilise la liste finale validée
                raw_text = "Terminé"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[92m{raw_text}\033[0m") # Vert
                details = f"{temps}x {fruit} prêt"
            else:
                status_text = f"{status:<20}"
                details = "-"
                
            print("| {:<13} | {:<10} | {} | {:<10} | {:<30} |".format(fruit, temps, status_text, worker, details))
            
        print(divider)
        
        # Barre de progression globale
        progress = (completed_count / cls.total_tasks) * 100
        filled = int(progress // 5)
        bar = "" * filled + "-" * (20 - filled)
        print(f"\nProgression globale : [{bar}] {progress:.0f}%")
        
        # Log des 5 derniers événements systèmes (timeouts, crashs, attributions)
        print("\n\033[1mHISTORIQUE DES ÉVÉNEMENTS SYSTEME (DEBUG) :\033[0m")
        if not cls.events:
            print("  En attente de l'activité des esclaves...")
        else:
            # On n'affiche que les 5 derniers messages pour garder la console propre
            for event in cls.events[-5:]:
                print(f"  {event}")
        sys.stdout.flush()

    def exposed_get_task(self, slave_id: str):
        with self.lock:
            now = time.time()
            
            # 1. Nettoyage et détection des Timeouts (Récupération des tâches perdues)
            for task in self.tasks:
                if task["status"] == "PROCESSING":
                    expected_duration = task["temps"] 
                    timeout_limit = expected_duration + 3 # 3 secondes de tolérance
                    
                    if now - task["start_time"] > timeout_limit:
                        # On log le timeout dans l'historique
                        msg = f"\033[91m[Timeout]\033[0m Slave {task['assigned_to']} injoignable sur '{task['fruit']}'. Réassignation."
                        self.events.append(msg)
                        
                        task["status"] = "PENDING"
                        task["assigned_to"] = None
                        task["start_time"] = None

            # 2. Recherche et attribution d'une tâche disponible
            for task in self.tasks:
                if task["status"] == "PENDING":
                    task["status"] = "PROCESSING"
                    task["assigned_to"] = slave_id
                    task["start_time"] = now
                    
                    self.events.append(f"\033[93m[Assigné]\033[0m Tâche '{task['fruit']}' attribuée au Slave {slave_id}")
                    self._print_dashboard()
                    return "PROCESS", (task["id"], task["fruit"], task["temps"])

            # 3. S'il reste des tâches actives, l'esclave doit attendre poliment
            any_processing = any(t["status"] == "PROCESSING" for t in self.tasks)
            if any_processing:
                return "WAIT", None

            # 4. Fin de service : plus aucune tâche à faire ni à surveiller
            return "SHUTDOWN", None

    def exposed_submit_result(self, slave_id: str, task_id: int, result: str):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    # Protection : Si le résultat est soumis après un timeout (le fruit a déjà été réattribué et fini)
                    if task["status"] == "COMPLETED":
                        msg = f"\033[90m[Ignoré]\033[0m Résultat tardif du Slave {slave_id} pour '{task['fruit']}'"
                        self.events.append(msg)
                        self._print_dashboard()
                        return
                    
                    task["status"] = "COMPLETED"
                    self.events.append(f"\033[92m[Reçu]\033[0m Slave {slave_id} a terminé la découpe de '{task['fruit']}'")
                    self.results.append(result)
                    self._print_dashboard()
                    
                    # Validation et arrêt propre une fois toutes les tâches complétées
                    if len(self.results) == self.total_tasks:
                        print("\n\033[92m\033[1mSUCCÈS : La salade de fruits résiliente est prête ! \033[0m\n")
                        sys.stdout.flush()
                        
                        def shutdown():
                            time.sleep(1.5)  # Permet aux derniers clients de fermer proprement
                            if MasterService.server_instance:
                                MasterService.server_instance.close()
                            os._exit(0)
                        threading.Thread(target=shutdown).start()

if __name__ == "__main__":
    # Affichage de départ avant l'arrivée des esclaves
    MasterService._print_dashboard()
    
    server = ThreadedServer(MasterService, port=18812, protocol_config={"allow_public_attrs": True})
    MasterService.server_instance = server
    server.start()
