# Seccion 2: Analisis de Codigo Concurrente

## Fragmento de Codigo: El Cajero Automatico

- **Problemas identificados:**
  - Existe una condicion de carrera sobre `saldo_cuenta`: la validacion `if saldo_cuenta >= monto` y la actualizacion `saldo_cuenta -= monto` no estan protegidas de forma atomica.
  - Se declara `lock_cuenta`, pero no se usa. Esto deja la seccion critica sin sincronizacion real.
  - `time.sleep(0.1)` dentro del flujo de retiro amplifica la ventana de interleaving entre hilos, haciendo mas probable el error.

- **Riesgos:**
  - Retiros aprobados sobre un saldo ya consumido por otro hilo (TOCTOU: time-of-check to time-of-use).
  - Saldo final inconsistente (por ejemplo, negativo o distinto al esperado segun reglas de negocio).
  - Comportamiento no determinista: ejecuciones identicas producen resultados diferentes.

- **Propuesta de correccion:**
  - Encapsular la operacion "verificar saldo + debitar" en una unica seccion critica protegida por `threading.Lock`.
  - Mantener `sleep` fuera de la parte critica si solo simula latencia externa, para no bloquear innecesariamente a otros hilos.
  - Implementacion propuesta en: `section-2/cajeroAutomatico_corregido.py`.

## Fragmento de Codigo: El Contador Compartido (con doble verificacion)

- **Problemas identificados:**
  - La logica `if not self.lock.locked():` es una doble verificacion insegura. Entre esa comprobacion y la adquisicion del lock puede intercalarse otro hilo.
  - Si el lock esta ocupado, el codigo hace `pass`, descartando el incremento. Esto viola la semantica del contador (se pierden eventos).
  - Se asume incorrectamente que "si otro hilo incrementa, este incremento ya no importa"; en concurrencia eso genera perdida sistematica de actualizaciones.

- **Riesgos:**
  - Resultado final menor al esperado (mucho menor que `10 * 100000`).
  - Errores silenciosos de contabilidad/metrica por perdida de operaciones.
  - Dependencia del scheduler: el bug aparece de forma intermitente y dificil de depurar.

- **Propuesta de correccion:**
  - El incremento debe ser siempre una operacion atomica: adquirir lock, incrementar, liberar lock.
  - Eliminar la rama `else: pass`; cada llamada a `incrementar()` debe reflejarse exactamente una vez.
  - Implementacion propuesta en: `section-2/contadorCompartido_corregido.py`.
