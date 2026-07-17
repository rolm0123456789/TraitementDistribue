# 2_master.py (Exercice 2 - Master de base)
import rpyc
from rpyc.utils.server import ThreadedServer
import os
import sys
import threading
import time

# Force stdout/stderr to UTF-8 to handle box-drawing, emojis, and accents on Windows/all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

FRUITS = [['pomme', 5], ['banane', 3], ['orange', 10], ['kiwi', 4], ['fraise', 3]]

class MasterService(rpyc.Service):
    lock = threading.Lock()
    
    # Structure de données partagée entre toutes les connexions RPyC
    tasks = {
        fruit: {
            "qty": qty,
            "status": "En attente",
            "worker": None,
            "result": "-"
        }
        for fruit, qty in FRUITS
    }
    
    total_tasks = len(FRUITS)
    completed_tasks = 0

    @classmethod
    def _print_dashboard(cls):
        """Efface la console et redessine le tableau de bord mis à jour."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("\n\033[1mSYSTÈME MASTER-SLAVE : PRÉPARATION DE LA SALADE\033[0m\n")
        
        # En-tête du tableau (Nouvelle colonne Slave ID de taille 10)
        divider = "+" + "-"*15 + "+" + "-"*12 + "+" + "-"*22 + "+" + "-"*12 + "+" + "-"*32 + "+"
        print(divider)
        print("| {:<13} | {:<10} | {:<20} | {:<10} | {:<30} |".format("Fruit", "Temps (s)", "Statut", "Slave ID", "Détails / Résultat"))
        print(divider)
        
        for fruit, info in cls.tasks.items():
            qty = info["qty"]
            status = info["status"]
            worker = info["worker"] if info["worker"] else "-"
            result = info["result"]
            
            # Application des couleurs ANSI sans décaler les colonnes
            if status == "En attente":
                raw_text = "En attente"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[94m{raw_text}...\033[0m") # Bleu
                details = "-"
            elif status == "En cours":
                raw_text = "En cours"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[93m{raw_text}\033[0m") # Jaune
                details = "Découpe en cours"
            else: # Terminé
                raw_text = "Terminé"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[92m{raw_text}\033[0m") # Vert
                details = result
                
            print("| {:<13} | {:<10} | {} | {:<10} | {:<30} |".format(fruit, qty, status_text, worker, details))
            
        print(divider)
        
        # Barre de progression dynamique
        progress = (cls.completed_tasks / cls.total_tasks) * 100
        filled = int(progress // 5)
        bar = "█" * filled + "-" * (20 - filled)
        print(f"\nProgression globale : [{bar}] {progress:.0f}%")
        sys.stdout.flush()

    def exposed_get_task(self, slave_id: str):
        """Distribue une tâche en attente et l'associe à l'ID de l'esclave."""
        with MasterService.lock:
            for fruit, info in MasterService.tasks.items():
                if info["status"] == "En attente":
                    info["status"] = "En cours"
                    info["worker"] = slave_id
                    MasterService._print_dashboard()
                    return [fruit, info["qty"]]
            return None

    def exposed_submit_result(self, slave_id: str, fruit_name: str, result: str):
        """Réceptionne le travail et conserve l'ID de l'esclave pour l'historique."""
        with MasterService.lock:
            if fruit_name in MasterService.tasks:
                if MasterService.tasks[fruit_name]["status"] == "Terminé":
                    return
                MasterService.tasks[fruit_name]["status"] = "Terminé"
                MasterService.tasks[fruit_name]["result"] = result
                MasterService.completed_tasks += 1
                MasterService._print_dashboard()
                
                if MasterService.completed_tasks == MasterService.total_tasks:
                    print("\n\033[92m\033[1mSUCCÈS : La salade de fruits est prête ! Bon appétit ! \033[0m\n")
                    sys.stdout.flush()
                    
                    def shutdown():
                        time.sleep(1)
                        os._exit(0)
                    threading.Thread(target=shutdown).start()

if __name__ == "__main__":
    MasterService._print_dashboard()
    server = ThreadedServer(MasterService, port=18812, protocol_config={"allow_public_attrs": True})
    server.start()
