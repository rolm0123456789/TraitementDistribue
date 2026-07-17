import rpyc
from rpyc.utils.server import ThreadedServer
import time
import sys
import threading
from threading import Timer

class MyService(rpyc.Service):

    def on_connect(self, conn):
        print("Client connected")

    def on_disconnect(self, conn):
        print("Client disconnected")

    def exposed_digest_value(self):
        # Return a random value
        return my_current_value
    
    def exposed_iter_value(self):
        # Return a random value
        return iteration

    def exposed_merge_value(self, other_value):
        global my_current_value
        if other_value is not None and other_value[1] > my_current_value[1]:
            my_current_value = other_value
        return my_current_value

if __name__ == "__main__":

    my_port = int(sys.argv[1])
    other_port = int(sys.argv[2])
    server = ThreadedServer(MyService, port=my_port)
    my_current_value = (
        sys.argv[3] if len(sys.argv) > 3 else None,
        time.time()
    )
    print("my_current_value:", my_current_value)
    iteration = 0

    print(f"Server started on port {my_port}")

    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    print("server started")
    connexion = False

    # Test de connexion à l'autre noeud
    while connexion == False:
        try:
            conn = rpyc.connect("localhost", other_port)
            connexion = True
        except ConnectionRefusedError:
            print(f"Waiting for the other node to start on port {other_port}...")
            time.sleep(1)

    #Boucle principale
    while True:
        
        #print(f"Iteration {iteration}:")
        iteration += 1
        #print("my_current_value:", my_current_value)

        time.sleep(1)  # Wait for a second before the next iteration
        other_current_value = conn.root.digest_value()
        my_current_value = conn.root.merge_value(my_current_value)
        


        