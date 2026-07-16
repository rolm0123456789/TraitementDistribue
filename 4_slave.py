# 4_slave.py (Exercice 4 - Slave Résilient)
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
            status, data = conn.root.get_task(slave_id)
        except (rpyc.core.protocol.PingError, EOFError, ConnectionResetError):
            print(f"[{slave_id}] Perte de connexion réseau avec le Master.")
            break
        
        if status == "SHUTDOWN":
            print(f"[{slave_id}] Fin de service. Déconnexion propre.")
            break
            
        elif status == "WAIT":
            # Attente active polie
            time.sleep(1)
            continue
            
        elif status == "PROCESS":
            task_id, fruit_name, temps = data
            print(f"[{slave_id}] Découpe de {fruit_name}...")
            
            time.sleep(temps)
            
            result = f"{fruit_name} découpé(e)(s) par {slave_id}"
            
            try:
                conn.root.submit_result(slave_id, task_id, result)
            except Exception as e:
                print(f"[{slave_id}] Échec de soumission du résultat (Master injoignable): {e}")
                break
                
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
print(f"Usage: python {sys.argv[0]} <slave_id>")
        sys.exit(1)
    main(sys.argv[1])
