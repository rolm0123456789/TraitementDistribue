import rpyc
from rpyc.utils.server import ThreadedServer
import time
import sys
import threading
import random

class MyService(rpyc.Service):

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass


    # PULL
    def exposed_digest_value(self):
        return my_current_value


    def exposed_iter_value(self):
        return iteration


    # PUSH + MERGE
    def exposed_receive_value(self, other_value):
        global my_current_value

        # garder la valeur la plus recente
        if (
            other_value is not None
            and other_value[1] > my_current_value[1]
        ):
            my_current_value = other_value

        return my_current_value



if __name__ == "__main__":


    my_port = int(sys.argv[1])
    all_ports = list(
        map(
            int,
            sys.argv[2].split(",")
        )
    )


    # valeur initiale
    my_current_value = (
        sys.argv[3] if len(sys.argv) > 3 else None,
        time.time()
    )

    iteration = 0


    server = ThreadedServer(
        MyService,
        port=my_port
    )


    print(
        f"Server started on port {my_port}"
    )

    print(
        "my_current_value:",
        my_current_value
    )


    server_thread = threading.Thread(
        target=server.start,
        daemon=True
    )

    server_thread.start()


    # boucle gossip push-pull

    while True:

        iteration += 1


        time.sleep(1)


        # choisir un voisin aléatoire
        other_port = random.choice(
            [
                p for p in all_ports
                if p != my_port
            ]
        )


        try:

            conn = rpyc.connect(
                "localhost",
                other_port
            )


            # ----------------
            # PULL
            # ----------------

            other_current_value = conn.root.digest_value()


            if (
                other_current_value is not None
                and other_current_value[1] < my_current_value[1]
            ):
                my_current_value = other_current_value



            # ----------------
            # PUSH
            # ----------------

            conn.root.receive_value(
                my_current_value
            )


            conn.close()



        except ConnectionRefusedError:

            pass



        print(
            f"Iteration {iteration}: {my_current_value}"
        )