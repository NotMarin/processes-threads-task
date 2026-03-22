"""
Sistema de Procesamiento de Vídeos con Prioridades
===================================================

Implementación de un sistema de transcodificación de video con:
- Cola de prioridad (Premium > Gratis)
- Sincronización thread-safe
- Mecanismo anti-inanición

Patrones de diseño aplicados:
- Producer-Consumer
- Monitor Pattern
"""

import threading
import time
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from collections import deque


class TipoCliente(Enum):
    """Enumera los tipos de clientes del sistema."""
    PREMIUM = "Premium"
    GRATIS = "Gratis"


@dataclass
class Trabajo:
    """Representa un trabajo de transcodificación de video."""
    id: str
    nombre_video: str
    cliente: str
    tipo: TipoCliente
    tiempo_procesamiento: float  # segundos simulados


class PriorityJobQueue:
    """
    Cola de trabajos con prioridad que implementa el Monitor Pattern.

    Características:
    - Dos niveles de prioridad (Premium > Gratis)
    - Thread-safe mediante Lock y Condition
    - Mecanismo anti-inanición con contador de trabajos premium consecutivos
    """

    MAX_CONSECUTIVE_PREMIUM = 3  # Máximo de trabajos premium consecutivos antes de forzar uno gratis

    def __init__(self):
        self.cola_premium: deque[Trabajo] = deque()
        self.cola_gratis: deque[Trabajo] = deque()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.shutdown_event = threading.Event()
        self.consecutive_premium_count = 0
        self.total_procesados = 0
        self.premium_procesados = 0
        self.gratis_procesados = 0
        self.anti_inanicion_activado = 0  # Contador de veces que se activó

    def agregar_trabajo(self, trabajo: Trabajo) -> None:
        """
        Agrega un trabajo a la cola correspondiente según su prioridad.
        Notifica a los workers que hay trabajo disponible.
        """
        with self.condition:
            if trabajo.tipo == TipoCliente.PREMIUM:
                self.cola_premium.append(trabajo)
            else:
                self.cola_gratis.append(trabajo)
            self.condition.notify()  # Despertar a un worker

    def obtener_trabajo(self) -> Optional[Trabajo]:
        """
        Obtiene el siguiente trabajo respetando prioridades y anti-inanición.

        Lógica de selección:
        1. Si se han procesado MAX_CONSECUTIVE_PREMIUM trabajos premium seguidos
           y hay trabajos gratis, se fuerza un trabajo gratis (anti-inanición)
        2. Si no, se toma de la cola premium si hay trabajos
        3. Si no hay premium, se toma de la cola gratis
        """
        with self.condition:
            while not self._hay_trabajos() and not self.shutdown_event.is_set():
                self.condition.wait(timeout=0.5)  # Timeout para verificar shutdown

            if self.shutdown_event.is_set() and not self._hay_trabajos():
                return None

            trabajo = None
            forzado_gratis = False

            # Mecanismo anti-inanición
            if (self.consecutive_premium_count >= self.MAX_CONSECUTIVE_PREMIUM
                and len(self.cola_gratis) > 0):
                trabajo = self.cola_gratis.popleft()
                self.consecutive_premium_count = 0
                self.gratis_procesados += 1
                self.anti_inanicion_activado += 1
                forzado_gratis = True
            # Prioridad normal: Premium primero
            elif len(self.cola_premium) > 0:
                trabajo = self.cola_premium.popleft()
                self.consecutive_premium_count += 1
                self.premium_procesados += 1
            # Si no hay premium, procesar gratis
            elif len(self.cola_gratis) > 0:
                trabajo = self.cola_gratis.popleft()
                self.consecutive_premium_count = 0
                self.gratis_procesados += 1

            if trabajo:
                self.total_procesados += 1

            return trabajo, forzado_gratis if trabajo else (None, False)

    def _hay_trabajos(self) -> bool:
        """Verifica si hay trabajos en alguna de las colas."""
        return len(self.cola_premium) > 0 or len(self.cola_gratis) > 0

    def iniciar_shutdown(self) -> None:
        """Señala a todos los workers que deben terminar."""
        with self.condition:
            self.shutdown_event.set()
            self.condition.notify_all()

    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas del procesamiento."""
        with self.lock:
            return {
                "total_procesados": self.total_procesados,
                "premium_procesados": self.premium_procesados,
                "gratis_procesados": self.gratis_procesados,
                "anti_inanicion_activaciones": self.anti_inanicion_activado,
                "cola_premium_pendiente": len(self.cola_premium),
                "cola_gratis_pendiente": len(self.cola_gratis)
            }


class Worker(threading.Thread):
    """
    Worker que consume trabajos de la cola de prioridad.
    Implementa el rol de Consumidor en el patrón Producer-Consumer.
    """

    def __init__(self, id: int, cola: PriorityJobQueue, log_lock: threading.Lock):
        super().__init__()
        self.id = id
        self.cola = cola
        self.log_lock = log_lock
        self.trabajos_procesados = 0

    def run(self) -> None:
        """Bucle principal del worker: obtener y procesar trabajos."""
        while not self.cola.shutdown_event.is_set() or self._hay_trabajos_pendientes():
            resultado = self.cola.obtener_trabajo()

            if resultado[0] is None:
                continue

            trabajo, forzado_gratis = resultado
            self._procesar_trabajo(trabajo, forzado_gratis)

    def _hay_trabajos_pendientes(self) -> bool:
        """Verifica si aún hay trabajos por procesar."""
        with self.cola.lock:
            return self.cola._hay_trabajos()

    def _procesar_trabajo(self, trabajo: Trabajo, forzado_gratis: bool) -> None:
        """Simula el procesamiento de un trabajo de transcodificación."""
        mensaje_extra = ""
        if forzado_gratis:
            mensaje_extra = " (Anti-inanición: forzado después de 3 premium consecutivos)"
        elif trabajo.tipo == TipoCliente.GRATIS:
            mensaje_extra = " (No hay premium en cola)"

        with self.log_lock:
            print(f"Worker-{self.id}: Procesando [{trabajo.nombre_video}] de {trabajo.cliente}{mensaje_extra}")

        # Simular tiempo de procesamiento
        time.sleep(trabajo.tiempo_procesamiento)

        with self.log_lock:
            print(f"Worker-{self.id}: Completado [{trabajo.nombre_video}] ({trabajo.tiempo_procesamiento:.2f}s)")

        self.trabajos_procesados += 1


class Cliente(threading.Thread):
    """
    Cliente que envía trabajos de transcodificación.
    Implementa el rol de Productor en el patrón Producer-Consumer.
    """

    def __init__(self, id: int, tipo: TipoCliente, cola: PriorityJobQueue,
                 log_lock: threading.Lock, num_trabajos: int):
        super().__init__()
        self.id = id
        self.tipo = tipo
        self.cola = cola
        self.log_lock = log_lock
        self.num_trabajos = num_trabajos
        self.nombre = f"Cliente-{tipo.value}-{id}"

    def run(self) -> None:
        """Envía trabajos a la cola de forma concurrente."""
        for i in range(1, self.num_trabajos + 1):
            # Crear trabajo con tiempo aleatorio de procesamiento
            trabajo = Trabajo(
                id=f"{self.nombre}-{i}",
                nombre_video=f"VIDEO-{self.tipo.value[0]}{self.id}-{i}",
                cliente=self.nombre,
                tipo=self.tipo,
                tiempo_procesamiento=random.uniform(0.1, 0.5)
            )

            self.cola.agregar_trabajo(trabajo)

            with self.log_lock:
                tipo_str = "PREMIUM" if self.tipo == TipoCliente.PREMIUM else "GRATIS"
                print(f"{self.nombre}: Envió trabajo [{trabajo.nombre_video}] [{tipo_str}]")

            # Pequeña pausa entre envíos para simular comportamiento real
            time.sleep(random.uniform(0.05, 0.2))


def main():
    """Función principal que orquesta el sistema de transcodificación."""

    print("=" * 70)
    print("    SISTEMA DE TRANSCODIFICACIÓN DE VIDEO CON PRIORIDADES")
    print("=" * 70)
    print()
    print("Configuración:")
    print(f"  - Clientes Premium: 3 (5-10 trabajos cada uno)")
    print(f"  - Clientes Gratis: 5 (5-10 trabajos cada uno)")
    print(f"  - Workers: 3")
    print(f"  - Anti-inanición: Forzar gratis después de 3 premium consecutivos")
    print()
    print("-" * 70)
    print("                        INICIO DEL PROCESAMIENTO")
    print("-" * 70)
    print()

    # Crear cola compartida
    cola = PriorityJobQueue()
    log_lock = threading.Lock()

    # Crear workers
    NUM_WORKERS = 3
    workers = [Worker(i + 1, cola, log_lock) for i in range(NUM_WORKERS)]

    # Crear clientes Premium (3 clientes, 5-10 trabajos cada uno)
    clientes_premium = [
        Cliente(i + 1, TipoCliente.PREMIUM, cola, log_lock, random.randint(5, 10))
        for i in range(3)
    ]

    # Crear clientes Gratis (5 clientes, 5-10 trabajos cada uno)
    clientes_gratis = [
        Cliente(i + 1, TipoCliente.GRATIS, cola, log_lock, random.randint(5, 10))
        for i in range(5)
    ]

    todos_clientes = clientes_premium + clientes_gratis

    # Iniciar workers primero
    for worker in workers:
        worker.start()

    # Pequeña pausa para que los workers estén listos
    time.sleep(0.1)

    # Iniciar clientes (envío concurrente de trabajos)
    for cliente in todos_clientes:
        cliente.start()

    # Esperar a que todos los clientes terminen de enviar
    for cliente in todos_clientes:
        cliente.join()

    print()
    print("-" * 70)
    print("Todos los clientes han terminado de enviar trabajos.")
    print("Esperando a que los workers completen el procesamiento...")
    print("-" * 70)
    print()

    # Dar tiempo para procesar trabajos pendientes, luego señalar shutdown
    while True:
        with cola.lock:
            if not cola._hay_trabajos():
                break
        time.sleep(0.1)

    # Señalar fin del sistema
    cola.iniciar_shutdown()

    # Esperar a que todos los workers terminen
    for worker in workers:
        worker.join()

    # Mostrar estadísticas finales
    stats = cola.obtener_estadisticas()

    print()
    print("=" * 70)
    print("                        ESTADÍSTICAS FINALES")
    print("=" * 70)
    print(f"  Total de trabajos procesados:      {stats['total_procesados']}")
    print(f"  Trabajos Premium procesados:       {stats['premium_procesados']}")
    print(f"  Trabajos Gratis procesados:        {stats['gratis_procesados']}")
    print(f"  Activaciones anti-inanición:       {stats['anti_inanicion_activaciones']}")
    print(f"  Trabajos Premium pendientes:       {stats['cola_premium_pendiente']}")
    print(f"  Trabajos Gratis pendientes:        {stats['cola_gratis_pendiente']}")
    print()
    print("  Trabajos procesados por worker:")
    for worker in workers:
        print(f"    Worker-{worker.id}: {worker.trabajos_procesados} trabajos")
    print("=" * 70)
    print()
    print("--- Sistema finalizado ---")


if __name__ == "__main__":
    main()
