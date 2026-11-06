# Tarea 3: combinar tableros y ramas

Implementa una versión MPI en esta carpeta. Reparte los IDs entre grupos de procesos y permite que los procesos de cada grupo exploren ramas distintas del tablero asignado.

Registra el tiempo total de los 30 IDs y explica cómo elegiste el tamaño de los grupos. Añade aquí el comando para ejecutar tu implementación con el contenedor. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, como en la calibración.

## Implementación

Archivo: `mpi_hibrido.py`. Usa `mpi_ramas.py`, que es una copia del archivo de `../mpi_por_ramas/` incluida en esta carpeta.

Los N procesos se dividen en grupos con `comm.Split`, y cada grupo tiene su propio comunicador. El proceso 0 de cada grupo es su líder.

- **Tableros entre grupos:** los IDs se reparten por turnos entre los grupos (el grupo *g* toma los IDs en las posiciones *g*, *g* + número de grupos, ...). Los grupos trabajan al mismo tiempo.
- **Ramas dentro de un grupo:** el líder procesa sus tableros en orden y reparte las ramas de cada uno entre los miembros de su grupo, con el mismo procedimiento de `mpi_por_ramas` (incluido el STOP al encontrar la solución).
- Al terminar, cada líder avisa a su grupo y todos los procesos se sincronizan con `comm.gather`; el tiempo total es el tiempo real hasta que termina el último grupo.

## Comando

Desde la raíz del repositorio (cmd de Windows). El tamaño de grupo elegido es 8 (por defecto el programa usa 4, así que `--grupo 8` es necesario):

```
docker run --rm -v "%cd%:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 16 python /app/mpi_hibrido/mpi_hibrido.py --all --grupo 8
```

En PowerShell o bash, reemplazar `%cd%` por `${PWD}`.

## Resultados

Con N = 16 y grupos de 8 procesos (2 grupos):

| Ejecución | Tiempo total (s) |
|---:|---:|
| 1 | 14.05 |
| 2 | 14.81 |
| 3 | 14.40 |
| **Mediana** | **14.40** |

En todas las ejecuciones se procesaron los 30 IDs (`Tableros procesados: 30 de 30`).

## Elección del tamaño de los grupos

Con N = 16 el tamaño de grupo debe dividir a 16 y ser al menos 2. En cada grupo el líder solo coordina, por lo que los procesos que resuelven son N menos el número de grupos. Se midió el tiempo total con distintos tamaños:

| Tamaño | Grupos | Procesos que resuelven | Tiempo total (s) |
|---:|---:|---:|---|
| 2 | 8 | 8 | 26.56 (1 ejecución) |
| 4 | 4 | 12 | 16.06 (1 ejecución) |
| 8 | 2 | 14 | 14.40 (mediana de 3; en una prueba previa dio 13.60) |
| 16 | 1 | 15 | 17.20 (equivale a `mpi_por_ramas`; mediana de 3) |

Con grupos pequeños muchos procesos solo coordinan y cada tablero recibe pocos procesos para sus ramas. Con grupos grandes cada tablero se resuelve con más procesos, pero se procesan menos tableros a la vez y aumenta el costo de comunicación y de espera por tablero. El mejor tiempo medido fue con grupos de 8, que es además el mayor tamaño que sigue combinando ambas estrategias (con 16 se vuelve a `mpi_por_ramas`). Se eligió el tamaño 8. La diferencia con el tamaño 4 es moderada (1.7 s, medida con una sola ejecución), mientras que frente a los tamaños 2 y 16 es clara.