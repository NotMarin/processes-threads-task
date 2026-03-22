"""
Simulación de conexión a servicio externo con timeout.
Usa threading.Timer para establecer un límite de tiempo.
"""

import threading
import time
import random


def conectar_a_servicio(resultado: list, evento_cancelacion: threading.Event):
    """
    Simula una operación de conexión con duración aleatoria.

    Args:
        resultado: Lista para almacenar el resultado de la conexión
        evento_cancelacion: Event para verificar si se debe cancelar
    """
    duracion = random.randint(1, 5)
    print(f"Simulando conexión por {duracion} segundos.")
    time.sleep(duracion)

    # Solo completar si no se canceló
    if not evento_cancelacion.is_set():
        print("Conexión completada.")
        resultado.append("Conectado")


def timeout_expirado(evento_cancelacion: threading.Event):
    """
    Función ejecutada cuando el timeout expira.

    Args:
        evento_cancelacion: Event para señalar la cancelación
    """
    print("Timeout: La conexión tardó demasiado. Operación cancelada.")
    evento_cancelacion.set()


def main():
    TIMEOUT_SEGUNDOS = 2.0

    # Crear evento de cancelación
    evento_cancelacion = threading.Event()

    # Lista para almacenar resultado (compartida entre hilos)
    resultado = []

    # Crear temporizador de timeout
    temporizador = threading.Timer(
        TIMEOUT_SEGUNDOS,
        timeout_expirado,
        args=[evento_cancelacion]
    )

    # Crear hilo de conexión
    hilo_conexion = threading.Thread(
        target=conectar_a_servicio,
        args=(resultado, evento_cancelacion)
    )

    print("Iniciando conexión...")

    # Iniciar temporizador y conexión
    temporizador.start()
    hilo_conexion.start()

    # Esperar a que termine la conexión
    hilo_conexion.join()

    # Verificar resultado
    if evento_cancelacion.is_set():
        # El timeout ocurrió
        temporizador.cancel()  # Por si aún no se ejecutó
    else:
        # La conexión fue exitosa antes del timeout
        temporizador.cancel()
        print(f"Conexión exitosa: {resultado[0]}.")


if __name__ == "__main__":
    main()
