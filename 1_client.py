# client_rpyc.py
import rpyc

def main():
    try:
        conn = rpyc.connect("localhost", 18812)
        # Appel transparent de la méthode exposée
        result = conn.root.get_value()
        print(f"Réponse RPyC : {result}")
        conn.close()
    except ConnectionRefusedError:
        print("Erreur : Impossible de se connecter au serveur RPyC.")

if __name__ == "__main__":
    main()