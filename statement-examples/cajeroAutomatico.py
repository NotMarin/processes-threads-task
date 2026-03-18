import threading
import time

saldo_cuenta = 1000
lock_cuenta = threading.Lock()

def retirar_dinero(cliente_id, monto):
    global saldo_cuenta
    print(f"Cliente {cliente_id} intenta retirar ${monto}...")
    if saldo_cuenta >= monto:
        # Simula el tiempo que toma la transacción
        time.sleep(0.1)
        saldo_cuenta -= monto
        print(f"Cliente {cliente_id} retiró ${monto}. Nuevo saldo: ${saldo_cuenta}")
    else:
        print(f"Cliente {cliente_id}: Fondos insuficientes. Saldo actual: ${saldo_cuenta}")

# Crear varios hilos de clientes
clientes = []
for i in range(5):
    t = threading.Thread(target=retirar_dinero, args=(i, 600))
    clientes.append(t)
    t.start()

for t in clientes:
    t.join()

print(f"Saldo final: ${saldo_cuenta}")