"""
Car Race Simulation using threading.Barrier
5 cars synchronize at the starting line before racing.
"""

import threading
import time
import random


def auto(id_auto: int, barrera: threading.Barrier):
    """
    Simulates a car arriving at the starting line and racing.

    Args:
        id_auto: Identifier for the car
        barrera: Barrier object for synchronization
    """
    # Simulate time to reach the starting line
    tiempo_llegada = random.uniform(0.5, 2.0)
    time.sleep(tiempo_llegada)

    print(f"Auto {id_auto} llegó a la salida y está esperando.")

    # Wait at the barrier until all cars arrive
    barrera.wait()

    # Race starts
    print(f"Auto {id_auto} inició la carrera.")


def main():
    NUM_AUTOS = 5

    # Create barrier with action to print separator when all cars arrive
    def accion_barrera():
        print("--- ¡CARRERA! ---")

    barrera = threading.Barrier(NUM_AUTOS, action=accion_barrera)

    # Create and start car threads
    hilos = []
    for i in range(NUM_AUTOS):
        hilo = threading.Thread(target=auto, args=(i + 1, barrera))
        hilo.start()
        hilos.append(hilo)

    # Wait for all threads to complete
    for hilo in hilos:
        hilo.join()

    print("\nCarrera finalizada.")


if __name__ == "__main__":
    main()
