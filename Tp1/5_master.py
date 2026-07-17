# master.py
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

# Configuration propre : chaque tâche possède un ID unique (0, 1, 2...)
# Format : [ID, Nom du fruit, Temps de découpe, [IDs des dépendances requises]]
FRUITS_CONFIG = [
    [0, 'pomme',  5,  []],
    [1, 'orange', 10, []],
    [2, 'banane', 3,  [0]],    # La banane (ID 2) attend la pomme (ID 0)
    [3, 'kiwi',   4,  [1]],    # Le kiwi (ID 3) attend l'orange (ID 1)
    [4, 'fraise', 2,  [2, 3]]  # La fraise (ID 4) attend la banane (2) et le kiwi (3)
]

class MasterService(rpyc.Service):
    lock = threading.Lock()
    events = []  # Logs pour le debug visuel
    results = []
    
    # Base de données d'état indexée par ID de tâche
    tasks = {
        item[0]: {
            "name": item[1],
            "qty": item[2],
            "status": "Verrouillé" if item[3] else "En attente",
            "dependencies": item[3],  # Liste d'IDs de dépendance
            "worker": None,
            "start_time": None,
            "result": "-"
        }
        for item in FRUITS_CONFIG
    }
    
    total_tasks = len(FRUITS_CONFIG)

    @classmethod
    def _print_dashboard(cls):
        """Efface la console et redessine le tableau de bord avec les IDs."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("\n\033[1mMASTER V3 : ORDONNANCEUR DE GRAPH PAR ID (RETRO-COMPATIBLE)\033[0m\n")
        
        # En-tête du tableau avec la colonne ID
        divider = "+" + "-"*5 + "+" + "-"*12 + "+" + "-"*12 + "+" + "-"*18 + "+" + "-"*10 + "+" + "-"*35 + "+"
        print(divider)
        print("| {:<3} | {:<10} | {:<10} | {:<16} | {:<8} | {:<33} |".format("ID", "Fruit", "Temps (s)", "Statut", "Slave ID", "Dépendances (IDs) / Infos"))
        print(divider)
        
        completed_count = sum(1 for t in cls.tasks.values() if t["status"] == "Terminé")
        
        for task_id, info in cls.tasks.items():
            name = info["name"]
            qty = info["qty"]
            status = info["status"]
            worker = info["worker"] if info["worker"] else "-"
            result = info["result"]
            deps = ", ".join(map(str, info["dependencies"])) if info["dependencies"] else "Aucune"
            
            # Application des couleurs ANSI
            if status == "Verrouillé":
                raw_text = "Verrouillé"
                padded = raw_text.ljust(16)
                status_text = padded.replace(raw_text, f"\033[90m{raw_text}\033[0m") # Gris
                details = f"Attend les IDs : {deps}"
            elif status == "En attente":
                raw_text = "En attente"
                padded = raw_text.ljust(16)
                status_text = padded.replace(raw_text, f"\033[94m{raw_text}...\033[0m") # Bleu
                details = "Prêt à être assigné"
            elif status == "En cours":
                raw_text = "En cours"
                padded = raw_text.ljust(16)
                status_text = padded.replace(raw_text, f"\033[93m{raw_text}\033[0m") # Jaune
                details = "Découpe active"
            else: # Terminé
                raw_text = "Terminé"
                padded = raw_text.ljust(16)
                status_text = padded.replace(raw_text, f"\033[92m{raw_text}\033[0m") # Vert
                details = result
                
            print("| {:<3} | {:<10} | {:<10} | {} | {:<8} | {:<33} |".format(task_id, name, qty, status_text, worker, details))
            
        print(divider)
        
        # Progression globale
        progress = (completed_count / cls.total_tasks) * 100
        filled = int(progress // 5)
        bar = "█" * filled + "-" * (20 - filled)
        print(f"\nProgression globale : [{bar}] {progress:.0f}%")
        
        # Affichage des 5 derniers événements
        print("\n\033[1mJOURNAL DE L'ORDONNANCEUR (ID-BASED) :\033[0m")
        if not cls.events:
            print("  En attente d'esclaves...")
        else:
            for event in cls.events[-5:]:
                print(f"  {event}")
        sys.stdout.flush()

    def exposed_get_task(self, slave_id=None):
        """Distribue une tâche prête. Accepte l'absence d'ID pour compatibilité V1."""
        worker_name = slave_id if slave_id else "Actif"
        
        while True:
            with self.lock:
                # 1. Vérification de fin globale
                all_completed = all(t["status"] == "Terminé" for t in self.tasks.values())
                if all_completed:
                    return None

                # 2. Détection et nettoyage des Timeouts
                now = time.time()
                for task_id, info in self.tasks.items():
                    if info["status"] == "En cours":
                        if now - info["start_time"] > info["qty"] + 4: # Marge de 4s
                            failed_worker = info["worker"]
                            info["status"] = "En attente"
                            info["worker"] = None
                            info["start_time"] = None
                            self.events.append(f"\033[91m[Timeout]\033[0m {failed_worker} a échoué sur la tâche {task_id} ({info['name']}).")
                            self._print_dashboard()

                # 3. Déverrouillage des tâches (Vérification des IDs requis)
                for task_id, info in self.tasks.items():
                    if info["status"] == "Verrouillé":
                        if all(self.tasks[dep_id]["status"] == "Terminé" for dep_id in info["dependencies"]):
                            info["status"] = "En attente"
                            self.events.append(f"\033[95m[Déverrouillé]\033[0m Tâche {task_id} ({info['name']}) prête.")
                            self._print_dashboard()

                # 4. Recherche et attribution d'une tâche "En attente"
                for task_id, info in self.tasks.items():
                    if info["status"] == "En attente":
                        info["status"] = "En cours"
                        info["worker"] = worker_name
                        info["start_time"] = now
                        self.events.append(f"\033[93m[Assigné]\033[0m Tâche {task_id} ({info['name']}) confiée à {worker_name}")
                        self._print_dashboard()
                        # Renvoie exactement ce que l'esclave V1 attend : [nom_du_fruit, temps]
                        return [info["name"], info["qty"]]

            # 5. Attente active si les tâches restantes sont encore verrouillées
            time.sleep(0.5)

    def exposed_submit_result(self, slave_id: str, result: str):
        """Réceptionne les résultats et fait correspondre le nom du fruit à son ID."""
        with self.lock:
            target_id = None
            
            # Recherche de la tâche associée en cherchant le nom du fruit dans la chaîne du résultat
            for task_id, info in self.tasks.items():
                if info["name"] in result:
                    target_id = task_id
                    break
            
            if target_id is None:
                self.events.append(f"\033[91m[Erreur]\033[0m Impossible d'associer le résultat de {slave_id} à une tâche : {result}")
                self._print_dashboard()
                return

            info = self.tasks[target_id]

            # Protection contre les retours tardifs post-timeout
            if info["status"] == "Terminé":
                self.events.append(f"\033[90m[Ignoré]\033[0m Résultat obsolète de {slave_id} pour la tâche {target_id} ({info['name']})")
                self._print_dashboard()
                return

            # Validation de la tâche
            info["status"] = "Terminé"
            info["worker"] = slave_id # Met à jour le vrai ID de l'esclave si "Actif" était temporaire
            info["result"] = result.strip()
            self.events.append(f"\033[92m[Reçu]\033[0m {slave_id} a complété la tâche {target_id} ({info['name']})")

            # Déverrouillage immédiat des tâches dépendantes
            for t_id, t_info in self.tasks.items():
                if t_info["status"] == "Verrouillé":
                    if all(self.tasks[dep_id]["status"] == "Terminé" for dep_id in t_info["dependencies"]):
                        t_info["status"] = "En attente"
                        self.events.append(f"\033[95m[Déverrouillé]\033[0m Tâche {t_id} ({t_info['name']}) débloquée.")

            self._print_dashboard()

            # Clôture propre une fois le graphe entièrement résolu
            completed_count = sum(1 for t in self.tasks.values() if t["status"] == "Terminé")
            if completed_count == self.total_tasks:
                print("\n\033[92m\033[1mSUCCÈS : Graphe d'ordonnancement par ID terminé avec succès ! \033[0m\n")
                sys.stdout.flush()

                def shutdown():
                    time.sleep(1.5)
                    os._exit(0)
                threading.Thread(target=shutdown).start()

if __name__ == "__main__":
    MasterService._print_dashboard()
    server = ThreadedServer(MasterService, port=18812, protocol_config={"allow_public_attrs": True})
    server.start()