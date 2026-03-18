import threading

contador = 0
lock = threading.Lock()

class ContadorSeguro:
    def __init__(self):
        self.valor = 0
        self.lock = threading.Lock()

    def incrementar(self):
        if not self.lock.locked():  # "Optimización" para no adquirir el lock si no es necesario
            with self.lock:
                self.valor += 1
        else:
            # Si está locked, asumimos que otro hilo ya está incrementando y no hacemos nada??
            pass

contador_obj = ContadorSeguro()

def tarea():
    for _ in range(100000):
        contador_obj.incrementar()

hilos = [threading.Thread(target=tarea) for _ in range(10)]
for h in hilos:
    h.start()
for h in hilos:
    h.join()

print(f"Valor final del contador: {contador_obj.valor}")