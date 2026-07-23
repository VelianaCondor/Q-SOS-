"""
motor.py

Lógica reusable del modelo de asignación depósito -> destino, para
CUALQUIER nodo (no un DESTINO fijo como en escenario_demo_chb.py).
La usan tanto el script de línea de comandos como la interfaz visual
(app.py), así no queda duplicada.

Requiere datos_recuperacion.py y depositos_cercanos.py en el mismo
directorio.
"""

from datos_recuperacion import LOGISTICA, ruta_mas_corta
from depositos_cercanos import depositos_mas_cercanos

CAPACIDAD_VEHICULO = {
    "camion_5T": 5000,
    "camion_2T": 2000,
    "camioneta_4x4": 800,
    "ambulancia": 300,
    "helicoptero": 1000,
}

_tipos_en_uso = {t for r in LOGISTICA.values() for t in r["vehiculos"]}
_tipos_faltantes = _tipos_en_uso - set(CAPACIDAD_VEHICULO)
if _tipos_faltantes:
    raise ValueError(f"Faltan capacidades en CAPACIDAD_VEHICULO para: {_tipos_faltantes}")


def demanda_comunidad(nodo_id):
    r = LOGISTICA[nodo_id]
    return r["agua"] + r["alimentos"] + r["primeros_auxilios"]


def construir_escenario(destino, n_depositos=6):
    depositos = depositos_mas_cercanos(destino, n=n_depositos)
    demanda_total = demanda_comunidad(destino)
    distancia = {dep: ruta_mas_corta(dep, destino)[1] for dep in depositos}
    pares = [
        (dep, t)
        for dep in depositos
        for t, c in LOGISTICA[dep]["vehiculos"].items()
        if c > 0
    ]
    disponible = {(dep, t): LOGISTICA[dep]["vehiculos"][t] for dep, t in pares}
    return {
        "destino": destino,
        "depositos": depositos,
        "demanda_total": demanda_total,
        "distancia": distancia,
        "pares": pares,
        "disponible": disponible,
    }


def resolver_optimo(escenario):
    """Programación dinámica: mínimo costo (distancia) para cubrir la
    demanda del destino. Ver escenario_demo_chb.py para la explicación
    completa de la técnica ("mínimo costo para cubrir al menos W").
    """
    distancia = escenario["distancia"]
    items = []
    for (dep, t), cant in escenario["disponible"].items():
        items += [(dep, t)] * cant

    W = escenario["demanda_total"]
    INF = float("inf")
    dp_prev = [INF] * (W + 1)
    dp_prev[0] = 0
    choice = [[False] * (W + 1) for _ in items]
    parent_c = [[None] * (W + 1) for _ in items]

    for i, (dep, t) in enumerate(items):
        w, costo = CAPACIDAD_VEHICULO[t], distancia[dep]
        dp_cur = dp_prev[:]
        for c_prev in range(W + 1):
            if dp_prev[c_prev] == INF:
                continue
            nc = min(c_prev + w, W)
            cand = dp_prev[c_prev] + costo
            if cand < dp_cur[nc]:
                dp_cur[nc], choice[i][nc], parent_c[i][nc] = cand, True, c_prev
        dp_prev = dp_cur

    if dp_prev[W] == INF:
        return None  # la flota candidata no alcanza -- prueba con más depósitos

    c, usados = W, []
    for i in range(len(items) - 1, -1, -1):
        if choice[i][c]:
            usados.append(items[i])
            c = parent_c[i][c]

    conteo = {}
    for par in usados:
        conteo[par] = conteo.get(par, 0) + 1

    total_km = sum(distancia[dep] * cant for (dep, t), cant in conteo.items())
    capacidad = sum(CAPACIDAD_VEHICULO[t] * cant for (dep, t), cant in conteo.items())
    return {
        "asignacion": conteo,
        "distancia_total": round(total_km, 2),
        "capacidad_cubierta": capacidad,
    }


def _empaquetar(escenario, conteo):
    distancia = escenario["distancia"]
    total_km = sum(distancia[dep] * cant for (dep, t), cant in conteo.items())
    capacidad = sum(CAPACIDAD_VEHICULO[t] * cant for (dep, t), cant in conteo.items())
    return {
        "asignacion": conteo,
        "distancia_total": round(total_km, 2),
        "capacidad_cubierta": capacidad,
    }


def construir_cqm(escenario):
    """Mismo CQM que en escenario_demo_chb.py: cuántos vehículos de cada
    tipo despachar desde cada depósito para cubrir la demanda del
    destino, minimizando distancia total.
    """
    from dimod import ConstrainedQuadraticModel, Integer, Binary, quicksum

    cqm = ConstrainedQuadraticModel()
    x = {}
    for dep, t in escenario["pares"]:
        cap = escenario["disponible"][(dep, t)]
        x[(dep, t)] = Binary(f"x_{dep}_{t}") if cap == 1 else Integer(
            f"x_{dep}_{t}", lower_bound=0, upper_bound=cap
        )
    cqm.set_objective(
        quicksum(escenario["distancia"][dep] * x[(dep, t)] for dep, t in escenario["pares"])
    )
    cqm.add_constraint(
        quicksum(CAPACIDAD_VEHICULO[t] * x[(dep, t)] for dep, t in escenario["pares"])
        >= escenario["demanda_total"],
        label="cobertura_demanda",
    )
    return cqm


def resolver_heuristico(escenario, num_reads=200, num_sweeps=500):
    """Simulated annealing local (dwave.samplers), sin nube -- el mismo
    tipo de heurística que usaría un solver cuántico/híbrido real. NO
    garantiza el óptimo, y esa brecha es justamente lo interesante de
    mostrar frente a resolver_optimo().
    """
    from dimod import cqm_to_bqm
    from dwave.samplers import SimulatedAnnealingSampler

    cqm = construir_cqm(escenario)
    bqm, invert = cqm_to_bqm(cqm)
    sampleset = SimulatedAnnealingSampler().sample(bqm, num_reads=num_reads, num_sweeps=num_sweeps)

    mejor_muestra, mejor_energia = None, None
    for s, en in zip(sampleset.record.sample, sampleset.record.energy):
        muestra = invert(dict(zip(sampleset.variables, s)))
        if cqm.check_feasible(muestra):
            if mejor_energia is None or en < mejor_energia:
                mejor_energia, mejor_muestra = en, muestra
    if mejor_muestra is None:
        return None

    conteo = {}
    for dep, t in escenario["pares"]:
        cant = int(round(mejor_muestra.get(f"x_{dep}_{t}", 0)))
        if cant > 0:
            conteo[(dep, t)] = cant
    return _empaquetar(escenario, conteo)


def resolver_leap(escenario):
    """D-Wave Leap real (requiere cuenta gratuita + token configurado:
    `dwave setup` o variable de entorno DWAVE_API_TOKEN). Solo se
    importa dwave.system aquí adentro para que el resto de la app
    funcione sin necesidad de credenciales.
    """
    from dwave.system import LeapHybridCQMSampler

    cqm = construir_cqm(escenario)
    sampleset = LeapHybridCQMSampler().sample_cqm(cqm)
    factibles = sampleset.filter(lambda d: d.is_feasible)
    if len(factibles) == 0:
        return None

    muestra = factibles.first.sample
    conteo = {}
    for dep, t in escenario["pares"]:
        cant = int(round(muestra.get(f"x_{dep}_{t}", 0)))
        if cant > 0:
            conteo[(dep, t)] = cant
    return _empaquetar(escenario, conteo)
