"""
Simulación de conexión a servicio externo con timeout.
Usa threading.Timer para establecer un límite de tiempo.
"""

import threading
import time
import random
from abc import ABC, abstractmethod


class EstrategiaResultadoConexion(ABC):
    @abstractmethod
    def manejar(self, resultado: list[str], temporizador: threading.Timer) -> None:
        pass


class EstrategiaTimeout(EstrategiaResultadoConexion):
    def manejar(self, resultado: list[str], temporizador: threading.Timer) -> None:
        temporizador.cancel()


class EstrategiaExito(EstrategiaResultadoConexion):
    def manejar(self, resultado: list[str], temporizador: threading.Timer) -> None:
        temporizador.cancel()
        print(f"Conexión exitosa: {resultado[0]}.")


class ManejadorResultado:
    def __init__(
        self,
        estrategia_timeout: EstrategiaResultadoConexion,
        estrategia_exito: EstrategiaResultadoConexion,
    ):
        self._estrategias = {
            True: estrategia_timeout,
            False: estrategia_exito,
        }

    def aplicar(
        self,
        timeout_ocurrio: bool,
        resultado: list[str],
        temporizador: threading.Timer,
    ) -> None:
        self._estrategias[timeout_ocurrio].manejar(resultado, temporizador)


class ConexionServicio:
    def __init__(self, timeout_segundos: float, manejador_resultado: ManejadorResultado):
        self.timeout_segundos = timeout_segundos
        self.manejador_resultado = manejador_resultado
        self.evento_cancelacion = threading.Event()
        self.resultado: list[str] = []

    def _conectar_a_servicio(self) -> None:
        duracion = random.randint(1, 5)
        print(f"Simulando conexión por {duracion} segundos.")
        time.sleep(duracion)

        if not self.evento_cancelacion.is_set():
            print("Conexión completada.")
            self.resultado.append("Conectado")

    def _timeout_expirado(self) -> None:
        print("Timeout: La conexión tardó demasiado. Operación cancelada.")
        self.evento_cancelacion.set()

    def ejecutar(self) -> None:
        temporizador = threading.Timer(self.timeout_segundos, self._timeout_expirado)
        hilo_conexion = threading.Thread(target=self._conectar_a_servicio)

        print("Iniciando conexión...")

        temporizador.start()
        hilo_conexion.start()
        hilo_conexion.join()

        self.manejador_resultado.aplicar(
            timeout_ocurrio=self.evento_cancelacion.is_set(),
            resultado=self.resultado,
            temporizador=temporizador,
        )


def main():
    timeout_segundos = 2.0

    manejador = ManejadorResultado(
        estrategia_timeout=EstrategiaTimeout(),
        estrategia_exito=EstrategiaExito(),
    )

    conexion = ConexionServicio(timeout_segundos, manejador)
    conexion.ejecutar()


if __name__ == "__main__":
    main()
