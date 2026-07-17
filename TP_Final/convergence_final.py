import sys
import subprocess
import time
import rpyc
import os

Nombre_de_noeuds = int(sys.argv[1])

python = sys.executable
script = os.path.join(os.path.dirname(__file__), "3_gossip_n.py")


processes = []

# Liste de tous les ports
ports = [
    18810 + i
    for i in range(Nombre_de_noeuds)
]

ports_str = ",".join(map(str, ports))


# Lancement des noeuds
for i in range(Nombre_de_noeuds):

    my_port = ports[i]

    p = subprocess.Popen(
        [
            python,
            script,
            str(my_port),
            ports_str,
            str(i)
        ]
    )

    processes.append(p)



current_values = [None] * Nombre_de_noeuds
iterations = [0] * Nombre_de_noeuds


try:

    while True:

        for i in range(Nombre_de_noeuds):

            my_port = ports[i]

            try:

                conn = rpyc.connect(
                    "localhost",
                    my_port
                )

                current_values[i] = conn.root.digest_value()
                iterations[i] = conn.root.iter_value()

                print(
                    f"Node {i}: value={current_values[i]}, iter={iterations[i]}"
                )

                conn.close()


            except ConnectionRefusedError:

                print(
                    f"Node {i} not ready"
                )



        if (
            all(value is not None for value in current_values)
            and all(
                value[0] == current_values[0][0]
                for value in current_values
            )
        ):

            print(
                f"Converged after {max(iterations)} iterations"
            )

            break



        time.sleep(1)



except KeyboardInterrupt:

    print("Stopping nodes...")



finally:

    for p in processes:
        p.terminate()


    for p in processes:
        p.wait()


    print("Done")