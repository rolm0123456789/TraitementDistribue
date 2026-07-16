# 2_slave.py (Exercice 2 - Slave de base)
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
        # On passe le slave_id pour que le Master l'affiche dans son tableau de bord
        task = conn.root.get_task(slave_id)
        
        if task is None:
            print(f"[{slave_id}] Plus de fruits à traiter. Déconnexion.")
            break
            
        fruit_name, temps = task
        print(f"[{slave_id}] Découpe de {temps}x {fruit_name}...")
        
        # Simulation du temps de traitement
        time.sleep(temps)
        
        result = f"{temps}x {fruit_name} prêt"
        
        # On informe le Master de l'identité du fruit traité pour le suivi
        conn.root.submit_result(slave_id, fruit_name, result)
        
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <slave_id>")
        sys.exit(1)
    main(sys.argv[1])
