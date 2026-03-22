# Sistema de Procesamiento de Vídeos con Prioridades

## 1. Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SISTEMA DE TRANSCODIFICACIÓN                    │
└─────────────────────────────────────────────────────────────────────────────┘

    PRODUCTORES (Clientes)                      CONSUMIDORES (Workers)
    ══════════════════════                      ══════════════════════

 ┌──────────────────────┐                      ┌──────────────────────┐
 │  Cliente-Premium-1   │──┐                ┌──│      Worker-1        │
 ├──────────────────────┤  │                │  └──────────────────────┘
 │  Cliente-Premium-2   │──┤                │  ┌──────────────────────┐
 ├──────────────────────┤  │                ├──│      Worker-2        │
 │  Cliente-Premium-3   │──┤                │  └──────────────────────┘
 └──────────────────────┘  │                │  ┌──────────────────────┐
                           │                └──│      Worker-3        │
 ┌──────────────────────┐  │                   └──────────────────────┘
 │  Cliente-Gratis-1    │──┤                          ▲
 ├──────────────────────┤  │                          │
 │  Cliente-Gratis-2    │──┤                          │
 ├──────────────────────┤  │    ┌─────────────────────┴─────────────────────┐
 │  Cliente-Gratis-3    │──┼───►│           COLA DE PRIORIDAD               │
 ├──────────────────────┤  │    │  ┌─────────────────────────────────────┐  │
 │  Cliente-Gratis-4    │──┤    │  │  Cola Premium (Alta Prioridad)      │  │
 ├──────────────────────┤  │    │  │  [VIDEO-P1] [VIDEO-P2] [VIDEO-P3]   │  │
 │  Cliente-Gratis-5    │──┘    │  └─────────────────────────────────────┘  │
 └──────────────────────┘       │  ┌─────────────────────────────────────┐  │
                                │  │  Cola Gratis (Baja Prioridad)       │  │
                                │  │  [VIDEO-G1] [VIDEO-G2] [VIDEO-G3]   │  │
                                │  └─────────────────────────────────────┘  │
                                │                                           │
                                │  ┌─────────────────────────────────────┐  │
                                │  │  Mecanismo Anti-Inanición           │  │
                                │  │  consecutive_premium_count = 0      │  │
                                │  │  MAX_CONSECUTIVE_PREMIUM = 3        │  │
                                │  └─────────────────────────────────────┘  │
                                └───────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                    PRIMITIVAS DE SINCRONIZACIÓN                      │
    │  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
    │  │    Lock     │  │   Condition     │  │        Event            │  │
    │  │ (Exclusión  │  │ (Espera/Señal   │  │   (Señal de parada)     │  │
    │  │   Mutua)    │  │  p/ Workers)    │  │                         │  │
    │  └─────────────┘  └─────────────────┘  └─────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────────┘
```

## 2. Justificación de Primitivas de Sincronización

### Lock (threading.Lock)
**Propósito**: Garantizar exclusión mutua en el acceso a la cola de trabajos.

**Justificación**:
- Múltiples clientes (productores) pueden intentar agregar trabajos simultáneamente
- Múltiples workers (consumidores) pueden intentar extraer trabajos simultáneamente
- El contador de trabajos premium consecutivos es un recurso compartido
- Sin un Lock, podrían ocurrir condiciones de carrera que corrompan el estado de la cola

**Uso**:
```python
with self.lock:
    # Acceso seguro a las colas y contadores
    self.premium_queue.append(job)
```

### Condition (threading.Condition)
**Propósito**: Coordinar la espera y notificación entre productores y consumidores.

**Justificación**:
- Los workers deben **esperar** cuando no hay trabajos disponibles (evita busy-waiting)
- Los clientes deben **notificar** a los workers cuando agregan un nuevo trabajo
- Condition encapsula un Lock y proporciona wait()/notify() para sincronización eficiente
- Más eficiente que polling continuo o sleep con verificación

**Uso**:
```python
# Worker esperando trabajo
with self.condition:
    while not hay_trabajo and not shutdown:
        self.condition.wait()

# Cliente notificando nuevo trabajo
with self.condition:
    self.agregar_trabajo(job)
    self.condition.notify()
```

### Event (threading.Event)
**Propósito**: Señalizar el fin del sistema de manera limpia.

**Justificación**:
- Necesitamos un mecanismo para indicar a todos los workers que deben terminar
- Event es thread-safe y permite verificación sin bloqueo
- Múltiples hilos pueden verificar el estado simultáneamente

**Uso**:
```python
# Verificar si debemos continuar
while not self.shutdown_event.is_set():
    # Procesar trabajos

# Señalar finalización
self.shutdown_event.set()
```

### ¿Por qué no usar queue.PriorityQueue directamente?
- `queue.PriorityQueue` de Python es thread-safe, pero no ofrece control granular sobre el mecanismo anti-inanición
- Necesitamos lógica personalizada para contar trabajos premium consecutivos
- Dos colas separadas (premium y gratis) con lógica de selección personalizada ofrecen más control

## 3. Implementación de Prioridades y Anti-Inanición

### Estrategia de Dos Colas
```
Cola Premium: [P1] [P2] [P3] ← Alta prioridad
Cola Gratis:  [G1] [G2] [G3] ← Baja prioridad
```

### Algoritmo de Selección de Trabajo

```python
def obtener_trabajo():
    if consecutive_premium_count >= MAX_CONSECUTIVE_PREMIUM:
        if cola_gratis_tiene_trabajos:
            consecutive_premium_count = 0
            return cola_gratis.pop()

    if cola_premium_tiene_trabajos:
        consecutive_premium_count += 1
        return cola_premium.pop()

    if cola_gratis_tiene_trabajos:
        consecutive_premium_count = 0
        return cola_gratis.pop()

    return None  # No hay trabajos
```

### Mecanismo Anti-Inanición: "Fairness After N"

**Parámetro**: `MAX_CONSECUTIVE_PREMIUM = 3`

**Funcionamiento**:
1. Cada vez que se procesa un trabajo Premium, incrementar contador
2. Si el contador alcanza el máximo (3), forzar procesamiento de trabajo Gratis (si existe)
3. Al procesar un trabajo Gratis, resetear contador a 0

**Ejemplo de Secuencia**:
```
Estado Inicial: consecutive_premium_count = 0

1. Llega P1 → Procesar P1 (count = 1)
2. Llega P2 → Procesar P2 (count = 2)
3. Llega G1 (espera)
4. Llega P3 → Procesar P3 (count = 3) ← MÁXIMO ALCANZADO
5. Llega P4 → Forzar G1 (count = 0) ← Anti-inanición activado
6. Procesar P4 (count = 1)
```

### Garantías del Sistema

1. **Prioridad Premium**: Los trabajos premium siempre tienen preferencia (excepto por anti-inanición)
2. **No-Inanición**: Ningún trabajo gratis esperará más de `MAX_CONSECUTIVE_PREMIUM` ciclos si hay workers disponibles
3. **Thread-Safety**: Todas las operaciones en la cola son atómicas gracias al Lock
4. **Eficiencia**: Workers duermen cuando no hay trabajo (no busy-waiting)

## 4. Patrones de Diseño Aplicados

### Producer-Consumer Pattern
- **Productores**: Clientes (Premium y Gratis) que generan trabajos
- **Consumidores**: Workers que procesan trabajos
- **Buffer**: Cola de prioridad compartida

### Monitor Pattern
- La clase `PriorityJobQueue` actúa como un monitor
- Encapsula los datos compartidos (colas) y la sincronización (lock, condition)
- Operaciones como `agregar_trabajo()` y `obtener_trabajo()` son métodos del monitor

### Template Method Pattern (implícito)
- Los clientes siguen el mismo "template" de comportamiento
- Solo varía el tipo de prioridad (Premium/Gratis)
