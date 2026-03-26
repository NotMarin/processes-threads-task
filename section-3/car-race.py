"""
Car Race Simulation using Observer pattern.
5 cars wait for a global start notification before racing.
"""

import random
import threading
import time
from typing import Callable


class Carrera:
    """Subject that notifies all cars when the race can start."""

    def __init__(self, total_autos: int):
        self.total_autos = total_autos
        self._llegadas = 0
        self._observadores: list[Callable[[], None]] = []
        self._lock = threading.Lock()

    def suscribir_inicio(self, observador: Callable[[], None]) -> None:
        self._observadores.append(observador)

    def registrar_llegada(self, id_auto: int) -> None:
        iniciar_carrera = False

        with self._lock:
            self._llegadas += 1
            print(f"Auto {id_auto} llegó a la salida y está esperando.")
            iniciar_carrera = self._llegadas == self.total_autos

        if iniciar_carrera:
            print("--- ¡CARRERA! ---")
            self._notificar_inicio()

    def _notificar_inicio(self) -> None:
        for observador in self._observadores:
            observador()


class Auto(threading.Thread):
    """Observer that waits for the race start notification."""

    def __init__(self, id_auto: int, carrera: Carrera):
        super().__init__()
        self.id_auto = id_auto
        self.carrera = carrera
        self._evento_inicio = threading.Event()
        self.carrera.suscribir_inicio(self._evento_inicio.set)

    def run(self) -> None:
        tiempo_llegada = random.uniform(0.5, 2.0)
        time.sleep(tiempo_llegada)

        self.carrera.registrar_llegada(self.id_auto)
        self._evento_inicio.wait()

        print(f"Auto {self.id_auto} inició la carrera.")


def main() -> None:
    num_autos = 5
    carrera = Carrera(num_autos)

    autos = [Auto(i + 1, carrera) for i in range(num_autos)]

    for auto in autos:
        auto.start()

    for auto in autos:
        auto.join()

    print("\nCarrera finalizada.")


if __name__ == "__main__":
    main()
