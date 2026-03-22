# Parcial 2 - Programacion Cliente/Servidor

Soluciones al segundo parcial del curso de Programacion Cliente/Servidor.

**Tema Principal**: Concurrencia, sincronizacion y patrones de diseno en Python con `threading`.

## Estructura del Proyecto

```
partial-2/
├── section-1/              # Preguntas teoricas
│   └── SECTION1.md
├── section-2/              # Analisis de codigo concurrente
│   ├── analisis-concurrencia.md
│   ├── cajeroAutomatico_corregido.py
│   └── contadorCompartido_corregido.py
├── section-3/              # Ejercicios practicos de sincronizacion
│   ├── car-race.py         # Barrier
│   ├── producer-consumer.py # Semaphores
│   └── connection.py       # Timer
├── section-4/              # Sistema de procesamiento con prioridades
│   ├── DESIGN.md
│   └── video_transcoder.py
└── statement-examples/     # Codigo original con errores (enunciado)
    ├── cajeroAutomatico.py
    ├── contadorCompartido.py
    └── sec1eje2.py
```

## Seccion 1: Preguntas Teoricas

Respuestas a conceptos fundamentales de concurrencia:

| Pregunta | Tema                                     |
| -------- | ---------------------------------------- |
| 1        | Concurrencia vs Paralelismo              |
| 2        | Condiciones de carrera (Race Conditions) |
| 3        | Deadlock vs Starvation                   |
| 4        | Procesos vs Hilos en servidores          |

**Archivo**: [`section-1/SECTION1.md`](section-1/SECTION1.md)

## Seccion 2: Analisis de Codigo Concurrente

Identificacion y correccion de problemas de concurrencia en codigo existente.

### Cajero Automatico

**Problema**: Race condition por falta de sincronizacion en operaciones de retiro.

```python
# ANTES (incorrecto)
if saldo_cuenta >= monto:   # <- Linea A
    time.sleep(0.1)
    saldo_cuenta -= monto   # <- Linea B
# Entre A y B otro hilo puede modificar saldo_cuenta
```

```python
# DESPUES (correcto)
with lock_cuenta:
    if saldo_cuenta >= monto:
        saldo_cuenta -= monto
```

### Contador Compartido

**Problema**: Doble verificacion insegura que descarta incrementos.

```python
# ANTES (incorrecto)
if not self.lock.locked():  # <- Race condition aqui
    with self.lock:
        self.valor += 1
else:
    pass  # <- Se pierden incrementos!
```

```python
# DESPUES (correcto)
with self.lock:
    self.valor += 1  # Siempre se ejecuta
```

**Archivos**:

- [`section-2/analisis-concurrencia.md`](section-2/analisis-concurrencia.md)
- [`section-2/cajeroAutomatico_corregido.py`](section-2/cajeroAutomatico_corregido.py)
- [`section-2/contadorCompartido_corregido.py`](section-2/contadorCompartido_corregido.py)

## Seccion 3: Ejercicios de Sincronizacion

Implementacion de primitivas de sincronizacion del modulo `threading`.

### 3.1 Carrera de Autos (`threading.Barrier`)

Sincroniza 5 autos para que inicien la carrera simultaneamente.

```
Auto 3 llego a la salida y esta esperando.
Auto 1 llego a la salida y esta esperando.
Auto 5 llego a la salida y esta esperando.
Auto 2 llego a la salida y esta esperando.
Auto 4 llego a la salida y esta esperando.
--- CARRERA! ---
Auto 4 inicio la carrera.
Auto 3 inicio la carrera.
...
```

### 3.2 Productor-Consumidor (`threading.Semaphore`)

Buffer acotado con semaforos para coordinar productores y consumidores.

| Primitiva      | Proposito                                 |
| -------------- | ----------------------------------------- |
| `empty_slots`  | Semaforo que cuenta espacios vacios       |
| `filled_slots` | Semaforo que cuenta elementos disponibles |
| `mutex`        | Lock para acceso exclusivo al buffer      |

### 3.3 Conexion con Timeout (`threading.Timer`)

Simula conexion a servicio externo con limite de tiempo configurable.

```
Iniciando conexion...
Simulando conexion por 4 segundos.
Timeout: La conexion tardo demasiado. Operacion cancelada.
```

**Archivos**:

- [`section-3/car-race.py`](section-3/car-race.py)
- [`section-3/producer-consumer.py`](section-3/producer-consumer.py)
- [`section-3/connection.py`](section-3/connection.py)

## Seccion 4: Sistema de Transcodificacion de Video

Sistema completo de procesamiento con colas de prioridad y mecanismo anti-inanicion.

### Arquitectura

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Clientes Premium   │────►│                     │────►│    Worker 1     │
│  (3 hilos)          │     │   Cola Prioridad    │     ├─────────────────┤
├─────────────────────┤     │   ┌─────────────┐   │     │    Worker 2     │
│  Clientes Gratis    │────►│   │ Premium     │   │     ├─────────────────┤
│  (5 hilos)          │     │   ├─────────────┤   │     │    Worker 3     │
└─────────────────────┘     │   │ Gratis      │   │     └─────────────────┘
                            │   └─────────────┘   │
                            └─────────────────────┘
```

### Caracteristicas

| Caracteristica  | Implementacion                           |
| --------------- | ---------------------------------------- |
| Thread-Safety   | `Lock` + `Condition`                     |
| Prioridad       | Dos colas separadas (Premium/Gratis)     |
| Anti-inanicion  | Contador de premium consecutivos (max 3) |
| Shutdown limpio | `Event` para senalizacion                |

### Patrones de Diseno

- **Producer-Consumer**: Clientes producen, Workers consumen
- **Monitor Pattern**: `PriorityJobQueue` encapsula datos + sincronizacion

### Ejecucion

```bash
python section-4/video_transcoder.py
```

**Salida esperada**:

```
Worker-1: Procesando [VIDEO-P1-1] de Cliente-Premium-1
Worker-2: Procesando [VIDEO-P2-1] de Cliente-Premium-2
Worker-3: Procesando [VIDEO-P3-1] de Cliente-Premium-3
Worker-2: Procesando [VIDEO-G1-1] de Cliente-Gratis-1 (Anti-inanicion: forzado despues de 3 premium consecutivos)
...
--- Sistema finalizado ---
```

**Archivos**:

- [`section-4/DESIGN.md`](section-4/DESIGN.md) - Diagrama y justificacion
- [`section-4/video_transcoder.py`](section-4/video_transcoder.py) - Implementacion

## Ejecucion de los Ejercicios

```bash
# Seccion 3
python section-3/car-race.py
python section-3/producer-consumer.py
python section-3/connection.py

# Seccion 4
python section-4/video_transcoder.py
```

## Resumen de Primitivas Utilizadas

| Primitiva             | Seccion | Uso                                  |
| --------------------- | ------- | ------------------------------------ |
| `threading.Lock`      | 2, 3, 4 | Exclusion mutua                      |
| `threading.Barrier`   | 3       | Sincronizacion de punto de encuentro |
| `threading.Semaphore` | 3       | Control de recursos limitados        |
| `threading.Timer`     | 3       | Ejecucion diferida con timeout       |
| `threading.Condition` | 4       | Wait/Notify para coordinacion        |
| `threading.Event`     | 3, 4    | Senalizacion entre hilos             |

## Requisitos

- Python 3.10+
- Sin dependencias externas (solo libreria estandar)
