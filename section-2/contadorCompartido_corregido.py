import threading


class ContadorSeguro:
    def __init__(self):
        self.valor = 0
        self.lock = threading.Lock()

    def incrementar(self):
        # El incremento completo debe ser atomico.
        with self.lock:
            self.valor += 1


contador_obj = ContadorSeguro()


def tarea():
    for _ in range(100000):
        contador_obj.incrementar()


hilos = [threading.Thread(target=tarea) for _ in range(10)]
for h in hilos:
    h.start()
for h in hilos:
    h.join()

esperado = 10 * 100000
print(f"Valor final del contador: {contador_obj.valor}")
print(f"Valor esperado: {esperado}")
