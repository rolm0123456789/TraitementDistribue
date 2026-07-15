# slave.py
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
        # Récupération active de la tâche (Pull)
        task = conn.root.get_task()
        
        if task is None:
            print(f"[{slave_id}] Plus de fruits à traiter. Déconnexion.")
            break
            
        fruit_name, temps = task
        print(f"[{slave_id}] Découpe de {temps}x {fruit_name}...")
        
        # Simulation du temps de traitement (0.1s par fruit)
        time.sleep(temps)
        
        result = f"{temps}x {fruit_name} découpé(e)(s) par {slave_id}"
        
        # Envoi du résultat au Master
        conn.root.submit_result(slave_id, result)
        
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slave.py <slave_id>")
        sys.exit(1)
    main(sys.argv[1])