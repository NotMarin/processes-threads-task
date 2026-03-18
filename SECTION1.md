# 1) Concurrencia vs. Paralelismo

**Diferencia fundamental**

- **Concurrencia**: es la capacidad de un sistema para gestionar varias tareas que progresan de forma solapada en el tiempo, aunque no necesariamente se ejecuten al mismo instante.
- **Paralelismo**: es la ejecución real y simultánea de varias tareas al mismo tiempo, normalmente usando varios núcleos de CPU.

**Ejemplos cotidianos (no informáticos)**

- **Concurrencia**: una persona cocina y, mientras hierve agua, corta verduras y revisa el horno. Alterna tareas; no hace dos acciones manuales exactamente al mismo tiempo.
- **Paralelismo**: dos cocineros trabajan en la misma cocina al mismo tiempo; uno prepara la salsa y el otro la pasta simultáneamente.

# 2) Condición de Carrera

**Definición**

Una **race condition** ocurre cuando dos o más hilos/procesos acceden y modifican estado compartido sin sincronización adecuada, y el resultado final depende del orden/timing no determinista de ejecución.

**Race condition en el código dado (`sec1eje2.py`)**

- La variable compartida es `contador_compartido`.
- Ambos hilos ejecutan `contador_compartido += 1` dentro de un bucle grande.
- Esa operación no es atómica: internamente implica leer el valor, sumarle 1 y escribirlo de vuelta.
- Si dos hilos intercalan esos pasos, se pueden perder incrementos (lost updates), por eso `Valor obtenido` puede ser menor que `2*NUM_INC`.

En resumen: el problema aparece porque hay **acceso concurrente de escritura sin lock** sobre una variable compartida.

# 3) Deadlock vs. Starvation

**Comparación**

- **Deadlock (interbloqueo)**: un conjunto de hilos/procesos queda bloqueado permanentemente porque cada uno espera un recurso retenido por otro (espera circular). Ninguno progresa.
- **Starvation (inanición)**: un hilo/proceso puede progresar teóricamente, pero en la práctica nunca obtiene CPU/recurso porque otros son favorecidos continuamente (políticas injustas o prioridad alta de otros).

**Mecanismo e impacto**

- Deadlock: bloqueo mutuo estructural; impacto fuerte e inmediato sobre las tareas involucradas.
- Starvation: bloqueo por falta de equidad; puede degradar latencia y causar espera indefinida para tareas de baja prioridad.

**¿Cuál es más fácil de prevenir?**

Generalmente, **el deadlock es más fácil de prevenir** en diseño porque existen reglas claras y verificables:

- orden global de adquisición de locks,
- timeouts al adquirir recursos,
- evitar hold-and-wait,
- reducción de secciones críticas.

La starvation es más sutil porque depende de planificación, carga dinámica y políticas de prioridad/equidad en tiempo de ejecución.

# 4) Procesos vs. Hilos en un Servidor con Múltiples Clientes

**Situación donde `multiprocessing` es mejor que `threading`**

Un servidor que atiende múltiples clientes y ejecuta tareas **CPU-bound** por solicitud (por ejemplo, cifrado pesado, compresión, análisis de imagen o inferencia numérica).

**Ventajas de usar procesos**

- Aprovechan múltiples núcleos con ejecución realmente paralela para trabajo CPU-bound.
- Aislamiento de memoria: si un proceso falla, es menos probable que derribe todo el servidor.
- Menor interferencia por estado compartido global (menos riesgos de race conditions entre workers si no se comparte memoria explícitamente).

**Desventaja**

- Mayor costo de recursos: más memoria, mayor overhead de creación y comunicación entre procesos (IPC), y complejidad adicional para compartir estado.
