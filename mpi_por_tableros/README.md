# Tarea 1: repartir tableros

Implementa una versión MPI en esta carpeta. Al ejecutar todos los tableros, cada ID debe ser una tarea que pueda asignarse a un proceso. Reutiliza el resolvedor de `../sudoku.py` y reúne los estados en el proceso coordinador.

Registra el tiempo total de ejecución y confirma que se procesaron los 30 IDs. Añade aquí el comando para ejecutar tu implementación con el contenedor. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, como en la calibración.

## Implementación

Archivo: `mpi_tableros.py`. El proceso 0 es el coordinador y los procesos 1 a N-1 son trabajadores. Cada ID de `seeds.txt` es una tarea: el coordinador envía un tablero a cada trabajador y, cada vez que uno termina y devuelve su estado (ID, resuelto, tiempo), le asigna el siguiente tablero pendiente. Así los trabajadores que reciben tableros fáciles toman más tableros y la carga se equilibra sola. Se reutiliza `resolver_con_tiempo` de `../sudoku.py`.

El tiempo total se mide en el coordinador con `MPI.Wtime()`, desde el primer envío hasta recibir el último resultado (tiempo real, no la suma de los tiempos parciales).

## Comando

Desde la raíz del repositorio (cmd de Windows):

```
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 16 python /app/mpi_por_tableros/mpi_tableros.py --all
```

En PowerShell o bash, reemplazar `%cd%` por `${PWD}`.

## Resultados

Con N = 16 (valor elegido en la calibración):

| Ejecución | Tiempo total (s) |
|---:|---:|
| 1 | 13.32 |
| 2 | 13.17 |
| 3 | 13.14 |
| **Mediana** | **13.17** |

En todas las ejecuciones se procesaron los 30 IDs (`Tableros procesados: 30 de 30`). Frente a la versión secuencial (mediana 80.49 s) el speedup es de 6.11x.