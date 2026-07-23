"""
depositos_cercanos.py

Calcula dinámicamente, usando el grafo real (ruta_mas_corta sobre
ARISTAS_BASE en datos_recuperacion.py), qué localidades están más
cerca de un epicentro y podrían actuar como depósito -- en vez de
tener la lista escrita a mano.

Requiere datos_recuperacion.py en el mismo directorio.
"""

from datos_recuperacion import NODOS, LOGISTICA, NOMBRES, ruta_mas_corta


def depositos_mas_cercanos(epicentro_id, n=6, solo_con_flota=True):
    """Devuelve los ids de las `n` localidades más cercanas a
    `epicentro_id` por distancia de RUTA real (no línea recta),
    ordenadas de más a menos cercana.

    epicentro_id : str
        Id del nodo epicentro (ej. "CHB").
    n : int
        Cuántas localidades candidatas devolver.
    solo_con_flota : bool
        Si True (default), descarta localidades sin ningún vehículo
        propio -- por más cerca que estén, no podrían enviar ayuda.
        Ponlo en False si quieres ver el ranking de cercanía puro,
        sin filtrar por capacidad.
    """
    candidatos = []
    for fila in NODOS:
        nid = fila[0]
        if nid == epicentro_id:
            continue
        if solo_con_flota and sum(LOGISTICA[nid]["vehiculos"].values()) == 0:
            continue
        _, km = ruta_mas_corta(epicentro_id, nid)
        candidatos.append((nid, km))

    candidatos.sort(key=lambda t: t[1])
    return [nid for nid, _ in candidatos[:n]]


def imprimir_ranking(epicentro_id, n=6, solo_con_flota=True):
    """Igual que depositos_mas_cercanos(), pero además imprime la
    distancia y la flota de cada uno -- útil para revisar a mano por
    qué entró (o no) cada localidad antes de usarlas en el CQM.
    """
    ids = depositos_mas_cercanos(epicentro_id, n=n, solo_con_flota=solo_con_flota)
    print(f"{n} localidades más cercanas a {NOMBRES[epicentro_id]} "
          f"({'con flota propia' if solo_con_flota else 'sin filtrar por flota'}):")
    for nid in ids:
        _, km = ruta_mas_corta(epicentro_id, nid)
        print(f"  {NOMBRES[nid]:<20} {km:>6} km   flota={LOGISTICA[nid]['vehiculos']}")
    return ids


if __name__ == "__main__":
    imprimir_ranking("CHB", n=6)
