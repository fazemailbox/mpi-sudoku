import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI
from baseline_secuencial import leer_seeds
from mpi_ramas import resolver_tablero, trabajador, TAG_FIN


def main():
    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    parser = argparse.ArgumentParser(description="MPI hibrido.")
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    parser.add_argument("--grupo", type=int, default=4,
                        help="procesos por grupo (debe dividir a N)")
    parser.add_argument("--all", action="store_true",
                        help="resolver todos los IDs (por defecto)")
    args = parser.parse_args()

    tam = args.grupo
    if tam < 2 or size % tam != 0:
        if rank == 0:
            print(f"El tamano de grupo debe ser >= 2 y dividir a N={size}.")
        return

    seeds = leer_seeds(args.archivo)
    id_grupo = rank // tam
    num_grupos = size // tam
    grupo = comm.Split(color=id_grupo, key=rank)

    comm.Barrier()
    inicio = MPI.Wtime()

    resultados = []
    if grupo.Get_rank() == 0:
        for nombre, tablero in list(seeds.items())[id_grupo::num_grupos]:
            resuelto, segundos = resolver_tablero(grupo, nombre, tablero)
            resultados.append((nombre, resuelto, segundos))
            print(f"\nID: {nombre}\n{'Resuelto' if resuelto else 'Sin solucion'}\n"
                  f"Tiempo parcial: {segundos:.6f} segundos (grupo {id_grupo})",
                  flush=True)
        for worker in range(1, tam):
            grupo.send(None, dest=worker, tag=TAG_FIN)
    else:
        trabajador(grupo)

    todos = comm.gather(resultados, root=0)
    if rank == 0:
        total = MPI.Wtime() - inicio
        hechos = sum(len(r) for r in todos)
        print(f"\nGrupos: {num_grupos} de {tam} procesos")
        print(f"Tableros procesados: {hechos} de {len(seeds)}")
        print(f"Tiempo total (real): {total:.6f} segundos")


if __name__ == "__main__":
    main()