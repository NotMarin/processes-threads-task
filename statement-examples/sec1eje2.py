import threading

contador_compartido = 0
NUM_INC = 1000000

def incrementar():
    global contador_compartido
    for _ in range(NUM_INC):
        contador_compartido += 1

hilo1 = threading.Thread(target=incrementar)
hilo2 = threading.Thread(target=incrementar)

hilo1.start()
hilo2.start()
hilo1.join()
hilo2.join()

print(f"Valor esperado: {2*NUM_INC}, Valor obtenido: {contador_compartido}")