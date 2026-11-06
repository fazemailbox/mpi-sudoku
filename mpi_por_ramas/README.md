# Tarea 2: repartir ramas de cada tablero

Implementa una versión MPI en esta carpeta. Con `--all`, el proceso coordinador lee los 30 IDs de `seeds.txt` en orden. Para cada tablero, crea tareas a partir de opciones válidas de las primeras casillas vacías y reparte esas ramas entre procesos. Espera a que termine ese tablero antes de comenzar el siguiente: **los tableros se procesan secuencialmente y las ramas de cada tablero en paralelo**.

Cada proceso explora su rama con backtracking y comunica el resultado. Cuando se encuentra una solución, los demás deben dejar de buscar ese tablero. Muestra el estado y el tiempo parcial de cada ID al terminarlo, además del tiempo total de los 30. Conserva la opción `--id` para resolver un solo tablero.

Añade aquí los comandos para ejecutar `--id` y `--all` con el contenedor. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, como en la calibración. Compara el tiempo total de `--all` con la versión secuencial y registra los resultados en `../INFORME.md`.

## Implementación

Archivo: `mpi_ramas.py`. El proceso 0 es el coordinador y procesa los tableros en orden, uno a la vez. Para cada tablero:

1. Rellena las primeras casillas vacías con todas las combinaciones válidas hasta tener al menos 4 ramas por trabajador (`RAMAS_POR_WORKER = 4`).
2. Reparte las ramas dinámicamente: cada trabajador recibe una, la explora con backtracking y devuelve el resultado; si no hay solución en esa rama, recibe otra.
3. Cuando un trabajador encuentra la solución, el coordinador descarta las ramas pendientes y envía un mensaje STOP (con el ID del tablero) a los trabajadores ocupados. Los trabajadores revisan si hay un STOP cada 2000 pasos de backtracking, por eso la búsqueda usa una copia cancelable del resolvedor que reutiliza `puede_colocar` de `../sudoku.py`.
4. Espera la respuesta de todos los trabajadores antes de pasar al siguiente tablero, e imprime el estado y el tiempo parcial del ID.

Al final de `--all` se imprime el tiempo total real. Se conserva la opción `--id` para resolver un solo tablero.

## Comandos

Desde la raíz del repositorio (cmd de Windows). Un solo tablero:

```
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 16 python /app/mpi_por_ramas/mpi_ramas.py --id 7
```

Todos los tableros:

```
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 16 python /app/mpi_por_ramas/mpi_ramas.py --all
```

En PowerShell o bash, reemplazar `%cd%` por `${PWD}`.

## Resultados

Con N = 16, tiempo total de `--all`:

| Ejecución | Tiempo total (s) |
|---:|---:|
| 1 | 17.20 |
| 2 | 16.39 |
| 3 | 17.20 |
| **Mediana** | **17.20** |

Frente a la versión secuencial (mediana 80.49 s) el speedup es de 4.68x. La comparación completa con las otras estrategias está en `../INFORME.md`.
