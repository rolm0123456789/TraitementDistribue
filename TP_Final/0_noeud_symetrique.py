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

    def exposed_propagate_value(self):
        # Simulate some processing time
        time.sleep(1)

        # Return a random value
        return my_current_value
        

if __name__ == "__main__":

    my_port = int(sys.argv[1])
    other_port = int(sys.argv[2])
    server = ThreadedServer(MyService, port=my_port)
    print(f"Server started on port {my_port}")

    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    print("server started")
    connexion = False

    while connexion == False:
        try:
            conn = rpyc.connect("localhost", other_port)
            connexion = True
        except ConnectionRefusedError:
            print(f"Waiting for the other node to start on port {other_port}...")
            time.sleep(1)

    my_current_value = sys.argv[3] if len(sys.argv) > 3 else None
    iteration = 0

    while True:
        
        print(f"Iteration {iteration}:")
        iteration += 1
        print("my_current_value:", my_current_value)

        
        other_current_value = conn.root.propagate_value()
        print("other_current_value:", other_current_value)
        if other_current_value == my_current_value and my_current_value is not None:

            timeout = 5
            t = Timer(timeout, print, ['Sorry, times up'])
            t.start()
            answer = input("enter a value to propagate :")
            if answer:
                print("You entered:", answer)
                my_current_value = answer
                answer = None
            t.cancel()


        else:
            print("Received value from other node:", other_current_value)
            my_current_value = other_current_value
            time.sleep(1)


        


        