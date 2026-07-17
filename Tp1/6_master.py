# 6_master.py (Exercice 6 - Arrêt propre si tous les slaves meurent)
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
    results = []
    events = []
    total_tasks = len(FRUITS)
    server_instance = None
    shutting_down = False

    # Suivi des esclaves vivants
    active_connections = set()       # objets connexion RPyC
    slave_to_conn = {}               # slave_id -> connexion
    had_slaves = False
    watchdog_started = False

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
    def _request_shutdown(cls, reason: str):
        """Planifie un arrêt propre du serveur (une seule fois)."""
        if cls.shutting_down:
            return
        cls.shutting_down = True
        cls.events.append(f"\033[91m[Arrêt]\033[0m {reason}")
        cls._print_dashboard()
        print(f"\n\033[91m\033[1m{reason}\033[0m")
        print("\033[1mFermeture propre du serveur Master...\033[0m\n")
        sys.stdout.flush()

        def shutdown():
            time.sleep(1.0)
            if MasterService.server_instance:
                try:
                    MasterService.server_instance.close()
                except Exception:
                    pass
            os._exit(0)

        threading.Thread(target=shutdown, daemon=True).start()

    @classmethod
    def _alive_slave_ids(cls):
        return set(cls.slave_to_conn.keys())

    @classmethod
    def _check_all_slaves_dead(cls):
        """Si des slaves ont existé et qu'il n'en reste plus, arrêter le serveur."""
        if cls.shutting_down:
            return
        if not cls.had_slaves:
            return
        if cls.active_connections or cls.slave_to_conn:
            return

        incomplete = any(t["status"] != "COMPLETED" for t in cls.tasks)
        if incomplete:
            reason = (
                "Tous les esclaves sont morts — tâches restantes abandonnées. "
                "Arrêt propre du serveur."
            )
        else:
            reason = "Tous les esclaves sont déconnectés — arrêt propre du serveur."
        cls._request_shutdown(reason)

    @classmethod
    def _release_tasks_of_slave(cls, slave_id: str):
        """Remet en PENDING les tâches encore PROCESSING du slave mort."""
        for task in cls.tasks:
            if task["status"] == "PROCESSING" and task["assigned_to"] == slave_id:
                task["status"] = "PENDING"
                task["assigned_to"] = None
                task["start_time"] = None
                cls.events.append(
                    f"\033[91m[Libéré]\033[0m Tâche '{task['fruit']}' libérée (slave {slave_id} mort)."
                )

    @classmethod
    def _unregister_slave(cls, slave_id: str, reason: str = "déconnecté"):
        if slave_id in cls.slave_to_conn:
            del cls.slave_to_conn[slave_id]
            cls.events.append(
                f"\033[91m[Mort]\033[0m Slave {slave_id} {reason}."
            )
            cls._release_tasks_of_slave(slave_id)

    @classmethod
    def _print_dashboard(cls):
        os.system('clear' if os.name == 'posix' else 'cls')

        print("\n\033[1mMASTER V6 : ARRÊT PROPRE SI TOUS LES SLAVES MEURENT\033[0m\n")

        alive_ids = sorted(cls._alive_slave_ids(), key=str)
        print(
            f"Esclaves actifs : \033[1m{len(alive_ids)}\033[0m  |  "
            f"Connexions RPyC : {len(cls.active_connections)}"
        )
        if alive_ids:
            print(f"IDs vivants : {', '.join(alive_ids)}")
        print()

        divider = (
            "+" + "-" * 15 + "+" + "-" * 12 + "+" + "-" * 22
            + "+" + "-" * 12 + "+" + "-" * 32 + "+"
        )
        print(divider)
        print("| {:<13} | {:<10} | {:<20} | {:<10} | {:<30} |".format(
            "Fruit", "Temps (s)", "Statut", "Slave ID", "Détails / Résultat"))
        print(divider)

        completed_count = 0
        for task in cls.tasks:
            fruit = task["fruit"]
            temps = task["temps"]
            status = task["status"]
            worker = task["assigned_to"] if task["assigned_to"] else "-"

            if status == "PENDING":
                raw_text = "En attente"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[94m{raw_text}...\033[0m")
                details = "-"
            elif status == "PROCESSING":
                raw_text = "En cours"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[93m{raw_text}\033[0m")
                details = "Découpe active"
            elif status == "COMPLETED":
                completed_count = len(cls.results)
                raw_text = "Terminé"
                padded = raw_text.ljust(20)
                status_text = padded.replace(raw_text, f"\033[92m{raw_text}\033[0m")
                details = f"{temps}x {fruit} prêt"
            else:
                status_text = f"{status:<20}"
                details = "-"

            print("| {:<13} | {:<10} | {} | {:<10} | {:<30} |".format(
                fruit, temps, status_text, worker, details))

        print(divider)

        progress = (completed_count / cls.total_tasks) * 100
        filled = int(progress // 5)
        bar = "█" * filled + "-" * (20 - filled)
        print(f"\nProgression globale : [{bar}] {progress:.0f}%")

        print("\n\033[1mHISTORIQUE DES ÉVÉNEMENTS SYSTEME :\033[0m")
        if not cls.events:
            print("  En attente de l'activité des esclaves...")
        else:
            for event in cls.events[-6:]:
                print(f"  {event}")
        sys.stdout.flush()

    @classmethod
    def _watchdog_loop(cls):
        """
        Filet de sécurité : si toutes les connexions sont tombées
        (ex. kill -9) sans on_disconnect immédiat, on arrête quand même.
        """
        while not cls.shutting_down:
            time.sleep(1.0)
            with cls.lock:
                # Nettoyer les connexions mortes encore référencées
                dead_conns = set()
                for conn in list(cls.active_connections):
                    try:
                        # closed peut exister selon la version de rpyc
                        if getattr(conn, "closed", False):
                            dead_conns.add(conn)
                    except Exception:
                        dead_conns.add(conn)

                for conn in dead_conns:
                    cls.active_connections.discard(conn)
                    slave_id = getattr(conn, "_slave_id", None)
                    if slave_id:
                        cls._unregister_slave(slave_id, reason="connexion morte (watchdog)")

                # Slaves mappés sur une connexion plus active
                for sid, conn in list(cls.slave_to_conn.items()):
                    if conn not in cls.active_connections:
                        cls._unregister_slave(sid, reason="connexion perdue (watchdog)")

                if dead_conns or True:
                    # Toujours vérifier l'extermination collective
                    if cls.had_slaves and not cls.active_connections and not cls.slave_to_conn:
                        cls._print_dashboard()
                        cls._check_all_slaves_dead()

    def on_connect(self, conn):
        # RPyC 6 n'injecte plus self._conn : on le mémorise nous-mêmes
        self.conn = conn
        with MasterService.lock:
            MasterService.active_connections.add(conn)
            MasterService.had_slaves = True
            MasterService.events.append(
                f"\033[96m[Connecté]\033[0m Nouvelle connexion "
                f"({len(MasterService.active_connections)} active(s))"
            )
            MasterService._print_dashboard()

            if not MasterService.watchdog_started:
                MasterService.watchdog_started = True
                threading.Thread(
                    target=MasterService._watchdog_loop,
                    daemon=True,
                ).start()

    def on_disconnect(self, conn):
        with MasterService.lock:
            MasterService.active_connections.discard(conn)
            slave_id = getattr(conn, "_slave_id", None)
            if slave_id:
                MasterService._unregister_slave(slave_id, reason="déconnecté")
            else:
                MasterService.events.append(
                    f"\033[91m[Déco]\033[0m Connexion perdue "
                    f"({len(MasterService.active_connections)} restante(s))"
                )

            MasterService._print_dashboard()
            MasterService._check_all_slaves_dead()

    def exposed_get_task(self, slave_id: str):
        with self.lock:
            if MasterService.shutting_down:
                return "SHUTDOWN", None

            # Enregistrement / heartbeat du slave (conn stockée dans on_connect)
            conn = getattr(self, "conn", None)
            if conn is not None:
                conn._slave_id = slave_id  # type: ignore[attr-defined]
                is_new = slave_id not in MasterService.slave_to_conn
                MasterService.slave_to_conn[slave_id] = conn
            else:
                is_new = False
            MasterService.had_slaves = True
            if is_new:
                MasterService.events.append(
                    f"\033[96m[Présent]\033[0m Slave {slave_id} enregistré."
                )

            now = time.time()

            # 1. Timeouts (esclave mort sans déconnexion propre)
            for task in self.tasks:
                if task["status"] == "PROCESSING":
                    timeout_limit = task["temps"] + 3
                    if now - task["start_time"] > timeout_limit:
                        dead = task["assigned_to"]
                        self.events.append(
                            f"\033[91m[Timeout]\033[0m Slave {dead} injoignable "
                            f"sur '{task['fruit']}'. Réassignation."
                        )
                        if dead in MasterService.slave_to_conn:
                            MasterService._unregister_slave(dead, reason="timeout")
                        else:
                            task["status"] = "PENDING"
                            task["assigned_to"] = None
                            task["start_time"] = None

                        MasterService._check_all_slaves_dead()
                        if MasterService.shutting_down:
                            return "SHUTDOWN", None

            # 2. Attribution d'une tâche PENDING
            for task in self.tasks:
                if task["status"] == "PENDING":
                    task["status"] = "PROCESSING"
                    task["assigned_to"] = slave_id
                    task["start_time"] = now
                    self.events.append(
                        f"\033[93m[Assigné]\033[0m Tâche '{task['fruit']}' "
                        f"attribuée au Slave {slave_id}"
                    )
                    self._print_dashboard()
                    return "PROCESS", (task["id"], task["fruit"], task["temps"])

            # 3. Tâches encore en cours ailleurs → attendre
            if any(t["status"] == "PROCESSING" for t in self.tasks):
                return "WAIT", None

            # 4. Plus rien à faire
            return "SHUTDOWN", None

    def exposed_submit_result(self, slave_id: str, task_id: int, result: str):
        with self.lock:
            if MasterService.shutting_down:
                return

            for task in self.tasks:
                if task["id"] == task_id:
                    if task["status"] == "COMPLETED":
                        self.events.append(
                            f"\033[90m[Ignoré]\033[0m Résultat tardif du Slave "
                            f"{slave_id} pour '{task['fruit']}'"
                        )
                        self._print_dashboard()
                        return

                    task["status"] = "COMPLETED"
                    self.events.append(
                        f"\033[92m[Reçu]\033[0m Slave {slave_id} a terminé "
                        f"la découpe de '{task['fruit']}'"
                    )
                    self.results.append(result)
                    self._print_dashboard()

                    if len(self.results) == self.total_tasks:
                        print(
                            "\n\033[92m\033[1mSUCCÈS : La salade de fruits est prête ! \033[0m\n"
                        )
                        sys.stdout.flush()
                        MasterService._request_shutdown(
                            "Toutes les tâches sont terminées — arrêt propre."
                        )
                    return


if __name__ == "__main__":
    MasterService._print_dashboard()
    server = ThreadedServer(
        MasterService,
        port=18812,
        protocol_config={"allow_public_attrs": True},
    )
    MasterService.server_instance = server
    print("\n[Master] En écoute sur le port 18812... (Ctrl+C pour quitter)\n")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Master] Interruption clavier — arrêt.")
    finally:
        try:
            server.close()
        except Exception:
            pass
