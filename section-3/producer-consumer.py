"""
Producer-Consumer Problem with Bounded Buffer
Using threading and semaphores for synchronization.
"""

import threading
import time
import random
from abc import ABC, abstractmethod
from collections import deque


class SharedBuffer:
    """Thread-safe bounded buffer using semaphores."""

    def __init__(self, size: int):
        self.size = size
        self.buffer = deque()
        self.mutex = threading.Lock()
        self.empty_slots = threading.Semaphore(size)  # Available slots
        self.filled_slots = threading.Semaphore(0)    # Items in buffer

    def put(self, item: "TaskCommand") -> list[str]:
        """Add an item to the buffer. Blocks if buffer is full."""
        self.empty_slots.acquire()  # Wait for an empty slot
        with self.mutex:
            self.buffer.append(item)
            buffer_snapshot = [elemento.label() for elemento in self.buffer]
        self.filled_slots.release()  # Signal that an item is available
        return buffer_snapshot

    def get(self) -> tuple["TaskCommand", list[str]]:
        """Remove and return an item from the buffer. Blocks if buffer is empty."""
        self.filled_slots.acquire()  # Wait for an item
        with self.mutex:
            item = self.buffer.popleft()
            buffer_snapshot = [elemento.label() for elemento in self.buffer]
        self.empty_slots.release()  # Signal that a slot is free
        return item, buffer_snapshot

    def current_state(self) -> list[str]:
        """Return a snapshot of the current buffer state."""
        with self.mutex:
            return [elemento.label() for elemento in self.buffer]


class TaskCommand(ABC):
    """Command interface for tasks consumed by worker threads."""

    @abstractmethod
    def execute(self, consumer_id: int, buffer: SharedBuffer) -> None:
        pass

    @abstractmethod
    def label(self) -> str:
        pass

    def is_stop(self) -> bool:
        return False


class ProcessTaskCommand(TaskCommand):
    def __init__(self, task_id: int):
        self.task_id = task_id

    def execute(self, consumer_id: int, buffer: SharedBuffer) -> None:
        print(f"Consumidor-{consumer_id}: Tomó tarea {self.task_id}. Procesando...")

        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)

        buffer_state = buffer.current_state()
        print(
            f"Consumidor-{consumer_id}: Terminó de procesar tarea {self.task_id}. "
            f"Buffer: {buffer_state}"
        )

    def label(self) -> str:
        return str(self.task_id)


class StopCommand(TaskCommand):
    def execute(self, consumer_id: int, buffer: SharedBuffer) -> None:
        return

    def label(self) -> str:
        return "STOP"

    def is_stop(self) -> bool:
        return True


def producer(buffer: SharedBuffer, num_tasks: int, num_consumers: int):
    """
    Producer function that generates commands and adds them to the buffer.

    Args:
        buffer: The shared buffer to add tasks to
        num_tasks: Number of tasks to produce
        num_consumers: Number of consumers to send stop commands to
    """
    for task_id in range(1, num_tasks + 1):
        # Simulate task generation time
        time.sleep(random.uniform(0.05, 0.2))

        comando = ProcessTaskCommand(task_id)
        buffer_state = buffer.put(comando)
        print(f"Productor: Tarea {task_id} añadida. Buffer: {buffer_state}")

    for _ in range(num_consumers):
        buffer.put(StopCommand())

    print("Productor: Terminó de producir todas las tareas.")


def consumer(consumer_id: int, buffer: SharedBuffer):
    """
    Consumer function that takes commands from the buffer and executes them.

    Args:
        consumer_id: Identifier for this consumer
        buffer: The shared buffer to take tasks from
    """
    while True:
        comando, _ = buffer.get()
        if comando.is_stop():
            break

        comando.execute(consumer_id, buffer)

    print(f"Consumidor-{consumer_id}: Terminó su trabajo.")


def main():
    # Configuration
    BUFFER_SIZE = 10
    NUM_TASKS = 20
    NUM_CONSUMERS = 2

    print(f"Iniciando sistema con buffer de tamaño {BUFFER_SIZE}")
    print(f"Produciendo {NUM_TASKS} tareas con {NUM_CONSUMERS} consumidores\n")

    # Create shared resources
    buffer = SharedBuffer(BUFFER_SIZE)

    # Create and start consumer threads
    consumer_threads = []
    for i in range(1, NUM_CONSUMERS + 1):
        t = threading.Thread(
            target=consumer,
            args=(i, buffer)
        )
        t.start()
        consumer_threads.append(t)

    # Create and start producer thread
    producer_thread = threading.Thread(
        target=producer,
        args=(buffer, NUM_TASKS, NUM_CONSUMERS)
    )
    producer_thread.start()

    # Wait for producer to finish
    producer_thread.join()

    # Wait for all consumers to finish
    for t in consumer_threads:
        t.join()

    print("\nTodas las tareas fueron producidas y consumidas.")


if __name__ == "__main__":
    main()
