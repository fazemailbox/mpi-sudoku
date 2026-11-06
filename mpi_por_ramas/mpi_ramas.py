import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI
from baseline_secuencial import leer_seeds
from sudoku import puede_colocar

TAG_TAREA = 1
TAG_RESULTADO = 2
TAG_STOP = 3
TAG_FIN = 4

RAMAS_POR_WORKER = 4
REVISAR_CADA = 2000


def primera_vacia(tablero):
    for f in range(9):
        for c in range(9):
            if tablero[f][c] == 0:
                return f, c
    return None


def expandir(ramas):
    nuevas = []
    for tablero in ramas:
        casilla = primera_vacia(tablero)
        if casilla is None:
            nuevas.append(tablero)
            continue
        f, c = casilla
        for valor in range(1, 10):
            if puede_colocar(tablero, f, c, valor):
                copia = [fila[:] for fila in tablero]
                copia[f][c] = valor
                nuevas.append(copia)
    return nuevas


def generar_ramas(tablero, minimo):
    ramas = [tablero]
    while ramas and len(ramas) < minimo and primera_vacia(ramas[0]) is not None:
        ramas = expandir(ramas)
    return ramas


class Cancelado(Exception):
    pass


def hay_stop(comm, id_tablero):
    while comm.Iprobe(source=0, tag=TAG_STOP):
        if comm.recv(source=0, tag=TAG_STOP) == id_tablero:
            return True
    return False


def resolver_cancelable(tablero, comm, id_tablero, contador):
    for fila in range(9):
        for columna in range(9):
            if tablero[fila][columna] != 0:
                continue
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    tablero[fila][columna] = valor
                    contador[0] += 1
                    if contador[0] % REVISAR_CADA == 0 and hay_stop(comm, id_tablero):
                        raise Cancelado
                    if resolver_cancelable(tablero, comm, id_tablero, contador):
                        return True
                    tablero[fila][columna] = 0
            return False
    return True


def resolver_tablero(comm, nombre, tablero):
    size = comm.Get_size()
    pendientes = generar_ramas(tablero, RAMAS_POR_WORKER * (size - 1))
    ocupados = set()
    solucion = None
    estado = MPI.Status()

    inicio = MPI.Wtime()

    for worker in range(1, size):
        if not pendientes:
            break
        comm.send((nombre, pendientes.pop(0)), dest=worker, tag=TAG_TAREA)
        ocupados.add(worker)

    while ocupados:
        encontrada, resultado = comm.recv(source=MPI.ANY_SOURCE,
                                          tag=TAG_RESULTADO, status=estado)
        worker = estado.Get_source()
        ocupados.discard(worker)

        if encontrada and solucion is None:
            solucion = resultado
            pendientes.clear()
            for otro in ocupados:
                comm.send(nombre, dest=otro, tag=TAG_STOP)

        if solucion is None and pendientes:
            comm.send((nombre, pendientes.pop(0)), dest=worker, tag=TAG_TAREA)
            ocupados.add(worker)

    return solucion is not None, MPI.Wtime() - inicio


def coordinador(comm, seleccionados, un_solo_id):
    inicio_total = MPI.Wtime()
    for nombre, tablero in seleccionados:
        resuelto, segundos = resolver_tablero(comm, nombre, tablero)
        print(f"\nID: {nombre}")
        print("Resuelto" if resuelto else "Sin solucion")
        etiqueta = "Tiempo" if un_solo_id else "Tiempo parcial"
        print(f"{etiqueta}: {segundos:.6f} segundos", flush=True)

    if not un_solo_id:
        print(f"\nTableros procesados: {len(seleccionados)}")
        print(f"Tiempo total (real): {MPI.Wtime() - inicio_total:.6f} segundos")


def trabajador(comm):
    estado = MPI.Status()
    while True:
        mensaje = comm.recv(source=0, tag=MPI.ANY_TAG, status=estado)
        tag = estado.Get_tag()
        if tag == TAG_FIN:
            break
        if tag == TAG_STOP:
            continue
        nombre, tablero = mensaje
        try:
            encontrada = resolver_cancelable(tablero, comm, nombre, [0])
        except Cancelado:
            encontrada = False
        comm.send((encontrada, tablero if encontrada else None),
                  dest=0, tag=TAG_RESULTADO)


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        if rank == 0:
            print("Se necesitan al menos 2 procesos (1 coordinador + 1 worker).")
        return

    if rank == 0:
        try:
            parser = argparse.ArgumentParser(description="MPI por ramas.")
            parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
            seleccion = parser.add_mutually_exclusive_group()
            seleccion.add_argument("--id", "--seed", dest="id",
                                   help="resolver solo la seed con este ID")
            seleccion.add_argument("--all", action="store_true",
                                   help="resolver todos los seeds")
            args = parser.parse_args()

            seeds = leer_seeds(args.archivo)
            if args.id:
                if args.id not in seeds:
                    parser.error(f"ID '{args.id}' no existe.")
                seleccionados = [(args.id, seeds[args.id])]
            else:
                seleccionados = list(seeds.items())
            coordinador(comm, seleccionados, bool(args.id))
        finally:
            for worker in range(1, size):
                comm.send(None, dest=worker, tag=TAG_FIN)
    else:
        trabajador(comm)


if __name__ == "__main__":
    main()