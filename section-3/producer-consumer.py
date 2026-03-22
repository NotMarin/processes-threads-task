"""
Producer-Consumer Problem with Bounded Buffer
Using threading and semaphores for synchronization.
"""

import threading
import time
import random
from collections import deque


class SharedBuffer:
    """Thread-safe bounded buffer using semaphores."""

    def __init__(self, size: int):
        self.size = size
        self.buffer = deque()
        self.mutex = threading.Lock()
        self.empty_slots = threading.Semaphore(size)  # Available slots
        self.filled_slots = threading.Semaphore(0)    # Items in buffer

    def put(self, item: int) -> list:
        """Add an item to the buffer. Blocks if buffer is full."""
        self.empty_slots.acquire()  # Wait for an empty slot
        with self.mutex:
            self.buffer.append(item)
            buffer_snapshot = list(self.buffer)
        self.filled_slots.release()  # Signal that an item is available
        return buffer_snapshot

    def get(self) -> tuple[int, list]:
        """Remove and return an item from the buffer. Blocks if buffer is empty."""
        self.filled_slots.acquire()  # Wait for an item
        with self.mutex:
            item = self.buffer.popleft()
            buffer_snapshot = list(self.buffer)
        self.empty_slots.release()  # Signal that a slot is free
        return item, buffer_snapshot

    def current_state(self) -> list:
        """Return a snapshot of the current buffer state."""
        with self.mutex:
            return list(self.buffer)


def producer(buffer: SharedBuffer, num_tasks: int, done_event: threading.Event):
    """
    Producer function that generates tasks and adds them to the buffer.

    Args:
        buffer: The shared buffer to add tasks to
        num_tasks: Number of tasks to produce
        done_event: Event to signal when production is complete
    """
    for task_id in range(1, num_tasks + 1):
        # Simulate task generation time
        time.sleep(random.uniform(0.05, 0.2))

        buffer_state = buffer.put(task_id)
        print(f"Productor: Tarea {task_id} añadida. Buffer: {buffer_state}")

    # Signal that production is complete
    done_event.set()
    print("Productor: Terminó de producir todas las tareas.")


def consumer(
    consumer_id: int,
    buffer: SharedBuffer,
    done_event: threading.Event,
    tasks_remaining: list,
    tasks_lock: threading.Lock
):
    """
    Consumer function that takes tasks from the buffer and processes them.

    Args:
        consumer_id: Identifier for this consumer
        buffer: The shared buffer to take tasks from
        done_event: Event indicating when production is complete
        tasks_remaining: Shared counter for remaining tasks
        tasks_lock: Lock for the tasks counter
    """
    while True:
        # Check if we should stop
        with tasks_lock:
            if tasks_remaining[0] <= 0 and done_event.is_set():
                break
            if tasks_remaining[0] <= 0:
                continue
            tasks_remaining[0] -= 1

        # Get task from buffer
        task_id, _ = buffer.get()
        print(f"Consumidor-{consumer_id}: Tomó tarea {task_id}. Procesando...")

        # Simulate task processing
        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)

        buffer_state = buffer.current_state()
        print(f"Consumidor-{consumer_id}: Terminó de procesar tarea {task_id}. Buffer: {buffer_state}")

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
    done_event = threading.Event()
    tasks_remaining = [NUM_TASKS]  # Using list to allow modification in threads
    tasks_lock = threading.Lock()

    # Create and start consumer threads
    consumer_threads = []
    for i in range(1, NUM_CONSUMERS + 1):
        t = threading.Thread(
            target=consumer,
            args=(i, buffer, done_event, tasks_remaining, tasks_lock)
        )
        t.start()
        consumer_threads.append(t)

    # Create and start producer thread
    producer_thread = threading.Thread(
        target=producer,
        args=(buffer, NUM_TASKS, done_event)
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
