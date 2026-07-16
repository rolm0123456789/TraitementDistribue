# 5_slave.py — Compatible avec 5_master.py (API rétro V1)
import rpyc
import time
import sys

def main(slave_id: str):
    print(f"[{slave_id}] Connexion au Master...")
    try:
        conn = rpyc.connect("localhost", 18812)
    except ConnectionRefusedError:
        print(f"[{slave_id}] Erreur : Impossible de joindre le Master.")
        sys.exit(1)

    while True:
        try:
            task = conn.root.get_task(slave_id)
        except (rpyc.core.protocol.PingError, EOFError, ConnectionResetError):
            print(f"[{slave_id}] Perte de connexion réseau avec le Master.")
            break

        if task is None:
            print(f"[{slave_id}] Plus de tâches à traiter. Déconnexion.")
            break

        fruit_name, temps = task
        print(f"[{slave_id}] Découpe de {fruit_name} ({temps}s)...")

        time.sleep(temps)

        result = f"{fruit_name} découpé(e)(s) par {slave_id}"

        try:
            conn.root.submit_result(slave_id, result)
        except Exception as e:
            print(f"[{slave_id}] Échec de soumission du résultat (Master injoignable): {e}")
            break

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 5_slave.py <slave_id>")
        sys.exit(1)
    main(sys.argv[1])
