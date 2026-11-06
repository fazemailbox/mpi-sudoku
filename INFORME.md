# Informe de resultados

Completa este informe después de implementar las tres tareas MPI. Ejecuta las comparaciones con el mismo archivo `seeds.txt`, en el mismo equipo y con el contenedor del taller.

## Entorno

- Equipo: Windows 10; AMD Ryzen 7 5800X3D (8 núcleos, 16 hilos lógicos); 32 GB de RAM; Docker versión 29.8.2
- Versión del contenedor: `augustosalazar/slim-mpi:2`
- Cantidad de repeticiones por medición: 3
- Valor común de `N` elegido: 16 (la calibración con `detectar_procesos_mpi.py` probó de N=1 a N=16 y recomendó 16)

## Comparación final con el mismo `N`

Repite tres veces cada ejecución y registra la mediana. Mantén fijo el `N` elegido en todas las filas MPI. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, igual que en la calibración, para permitir valores de `N` mayores que los slots detectados.

| Implementación   | Caso                               | Procesos | Mediana del tiempo total (s) | Aceleración frente a secuencial |
|------------------|------------------------------------|---------:|-----------------------------:|--------------------------------:|
| Secuencial       | Todos los IDs                      | 1        | 80,49                        | 1,00                            |
| MPI por tableros | Todos los IDs                      | 16       | 13,17                        | 6,11                            |
| MPI por ramas    | Todos los IDs, uno después de otro | 16       | 17,20                        | 4,68                            |
| MPI híbrido      | Todos los IDs                      | 16       | 14,40                        | 5,59                            |

Calcula la aceleración como `tiempo secuencial / tiempo MPI`. Mide el tiempo MPI desde el inicio del reparto hasta recibir todos los resultados necesarios.

Tiempos de las tres repeticiones (s):

| Implementación   | Ejecución 1 | Ejecución 2 | Ejecución 3 |
|------------------|------------:|------------:|------------:|
| Secuencial       | 80,49       | 80,78       | 79,96       |
| MPI por tableros | 13,32       | 13,17       | 13,14       |
| MPI por ramas    | 17,20       | 16,39       | 17,20       |
| MPI híbrido      | 14,05       | 14,81       | 14,40       |

El híbrido se ejecutó con N = 16 y grupos de 8 procesos (2 grupos). La elección del tamaño de grupo se justifica en `mpi_hibrido/README.md`. Todas las ejecuciones MPI procesaron los 30 IDs.

## Conclusiones

- **¿Qué estrategia obtuvo el menor tiempo para los 30 tableros? ¿Cuánto mejoró respecto a la versión secuencial?** La estrategia por tableros fue la más rápida: 13,17 s frente a 80,49 s de la versión secuencial, una aceleración de 6,11 (el tiempo se redujo cerca de un 84 %). Le siguieron el híbrido (14,40 s, aceleración 5,59) y las ramas (17,20 s, aceleración 4,68). Las tres versiones mejoran claramente a la secuencial.

- **¿Cómo afectaron la comunicación y las diferencias de duración entre tableros?** Los tableros no tardan lo mismo: en las ejecuciones se observan tableros desde unos 3 s hasta cerca de 11 s. En el reparto por tableros la comunicación es mínima (un mensaje de ida y otro de vuelta por tablero) y la asignación dinámica evita que un proceso acumule los tableros difíciles. Aun así, el tiempo total no puede bajar del tiempo del tablero más lento: con 15 trabajadores el ideal sería 80,49 / 15 ≈ 5,4 s, pero un solo tablero de unos 10,8 s ya supera ese valor, y el resultado de 13,17 s queda cerca de ese límite. En el reparto por ramas, el envío de ramas, el aviso de parada y la espera de que todos los trabajadores respondan se repiten en cada uno de los 30 tableros, y la rama que contiene la solución la resuelve un solo proceso; en los tableros cortos ese costo fijo es comparable a lo que se ahorra. En el híbrido, además, los tableros se asignan a los grupos de forma fija, así que el grupo que recibe los tableros más difíciles determina el tiempo total.

- **¿Cómo se comparó repartir tableros con resolverlos en orden y repartir las ramas de cada uno?** Repartir tableros fue mejor en este conjunto: es un paralelismo grueso, casi sin comunicación, y 30 tareas bastan para mantener ocupados a los 15 trabajadores. Resolver los tableros en orden y repartir sus ramas reduce mucho el tiempo de cada tablero (en el híbrido con grupos de 8 los tableros tardaron alrededor de 0,6 a 1,1 s, frente a 2 a 10 s en secuencial), pero paga la sincronización 30 veces y deja la solución de cada tablero limitada por su rama más larga. El híbrido quedó en un punto intermedio (14,40 s) y dependió del tamaño de grupo: 26,56 s con grupos de 2, 16,06 s con 4, 14,40 s con 8 y 17,20 s con 16, que equivale a `mpi_por_ramas`. No superó al reparto por tableros porque en cada grupo un proceso solo coordina (con grupos de 8 resuelven 14 de 16 procesos) y porque la asignación de tableros a grupos es fija. Es de esperar que combinar ambas estrategias convenga más cuando hay pocos tableros o uno domina el tiempo total, pero eso no se probó aquí.

Limitaciones: cada tiempo es la mediana de 3 ejecuciones en un solo equipo. La exploración de tamaños de grupo 2, 4 y 8 se hizo con una sola ejecución por tamaño, por lo que la diferencia entre 4 y 8 (1,7 s) es moderada, mientras que frente a 2 y 16 es clara.