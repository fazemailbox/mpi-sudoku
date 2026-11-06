import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI
from baseline_secuencial import leer_seeds
from sudoku import resolver_con_tiempo

TAG_TAREA = 1
TAG_RESULTADO = 2
TAG_FIN = 3


def coordinador(comm, seeds):
    size = comm.Get_size()
    pendientes = list(seeds.items())
    resultados = {}
    estado = MPI.Status()
    activos = 0

    inicio = MPI.Wtime()

    for worker in range(1, size):
        if pendientes:
            comm.send(pendientes.pop(0), dest=worker, tag=TAG_TAREA)
            activos += 1
        else:
            comm.send(None, dest=worker, tag=TAG_FIN)

    while activos > 0:
        nombre, resuelto, segundos = comm.recv(
            source=MPI.ANY_SOURCE, tag=TAG_RESULTADO, status=estado)
        worker = estado.Get_source()
        resultados[nombre] = (resuelto, segundos)

        print(f"\nID: {nombre}")
        print("Resuelto" if resuelto else "Sin solucion")
        print(f"Tiempo parcial: {segundos:.6f} segundos (proceso {worker})",
              flush=True)

        if pendientes:
            comm.send(pendientes.pop(0), dest=worker, tag=TAG_TAREA)
        else:
            comm.send(None, dest=worker, tag=TAG_FIN)
            activos -= 1

    total = MPI.Wtime() - inicio

    print(f"\nTableros procesados: {len(resultados)} de {len(seeds)}")
    print(f"Tiempo total (real): {total:.6f} segundos")


def trabajador(comm):
    estado = MPI.Status()
    while True:
        tarea = comm.recv(source=0, tag=MPI.ANY_TAG, status=estado)
        if estado.Get_tag() == TAG_FIN:
            break
        nombre, tablero = tarea
        resuelto, segundos = resolver_con_tiempo(tablero)
        comm.send((nombre, resuelto, segundos), dest=0, tag=TAG_RESULTADO)


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if comm.Get_size() < 2:
        if rank == 0:
            print("Se necesitan al menos 2 procesos (1 coordinador + 1 worker).")
        return

    if rank == 0:
        parser = argparse.ArgumentParser(description="MPI por tableros.")
        parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
        parser.add_argument("--all", action="store_true",
                            help="resolver todos los tableros (por defecto)")
        args = parser.parse_args()
        coordinador(comm, leer_seeds(args.archivo))
    else:
        trabajador(comm)


if __name__ == "__main__":
    main()