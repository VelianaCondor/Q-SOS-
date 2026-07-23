"""
datos_recuperacion.py

Dataset consolidado de logística de emergencia (escenario: sismo con
epicentro aproximado en Chupaca) para las provincias de Huancayo, Chupaca
y Concepción (Junín, Perú).

    NODOS                 -> lista cruda (id, nombre, tipo, provincia, lat, lon, fuente_coord)
    COORDS / NOMBRES       -> lookups rápidos por id de nodo
    LOGISTICA              -> inventario por nodo (agua, alimentos, primeros_auxilios,
                               vehiculos, hospitales, centros_salud)
    ARISTAS                -> tramos de carretera con distancia_km y estado_via
    ADYACENCIA             -> lista de adyacencia no dirigida (para armar rutas)
    HOSPITALES             -> establecimientos de salud detallados (DIRESA/EsSalud)
    PRIORIDAD_COMUNIDADES  -> ranking de urgencia por comunidad
    NODOS_INFO             -> vista consolidada por nodo (todo lo anterior en un solo dict)
    FLOTA_TOTAL            -> conteo total de vehículos disponibles por tipo
    construir_grafo()      -> devuelve un networkx.Graph listo para el optimizador
                               (rutas, asignación de vehículos, minimización de tiempo)

No escribe ningún archivo en disco al importarse; todo queda en memoria.
"""

import math

# 1. NODOS (localidades)
NODOS = [
    # id, nombre, tipo, provincia, lat, lon, fuente_coord
    ("HYO",  "Huancayo",                 "capital_departamental", "Huancayo",   -12.0654, -75.2049, "mapa+geo"),
    ("ETB",  "El Tambo",                 "capital_distrital",     "Huancayo",   -12.0432, -75.2210, "mapa+geo"),
    ("CHI",  "Chilca",                   "capital_distrital",     "Huancayo",   -12.0797, -75.1994, "mapa+geo"),
    ("HCN",  "Huancán",                  "capital_distrital",     "Huancayo",   -12.0917, -75.1975, "mapa+geo"),
    ("HYC",  "Huayucachi",               "capital_distrital",     "Huancayo",   -12.1103, -75.2244, "mapa+geo"),
    ("VIQ",  "Viques",                   "capital_distrital",     "Huancayo",   -12.1364, -75.2367, "mapa+geo"),
    ("HCP",  "Huacrapuquio",             "capital_distrital",     "Huancayo",   -12.1544, -75.2306, "estimada"),
    ("CHU_P","Chupuro",                  "capital_distrital",     "Huancayo",   -12.1358, -75.2536, "estimada"),
    ("SAP",  "Sapallanga",               "capital_distrital",     "Huancayo",   -12.1114, -75.1928, "mapa+geo"),
    ("PUC",  "Pucará",                   "capital_distrital",     "Huancayo",   -12.1444, -75.1519, "mapa+geo"),
    ("3DIC", "3 de Diciembre",           "poblado",               "Huancayo",   -12.1244, -75.2517, "estimada"),
    ("PAC",  "Pacacchaca",               "poblado",               "Huancayo",   -12.1181, -75.2597, "estimada"),
    ("HCOL", "Hacienda Colombina",       "poblado",               "Huancayo",   -12.1017, -75.2119, "estimada"),
    ("COCH", "Cochas Chico",             "poblado",               "Huancayo",   -11.9911, -75.1672, "estimada"),
    ("QUIL", "Quilcas",                  "capital_distrital",     "Huancayo",   -11.9508, -75.2381, "mapa+geo"),
    ("SANO", "Saño",                     "poblado",               "Huancayo",   -11.9800, -75.2444, "estimada"),
    ("HUAL", "Hualhuas",                 "capital_distrital",     "Huancayo",   -11.9800, -75.2611, "mapa+geo"),
    ("SAGU", "San Agustín",              "capital_distrital",     "Huancayo",   -12.0056, -75.2439, "estimada"),
    ("SJT",  "San Jerónimo de Tunán",    "capital_distrital",     "Huancayo",   -11.9578, -75.2825, "mapa+geo"),

    ("CHP",  "Chupaca",                  "capital_provincial",    "Chupaca",    -12.0672, -75.2892, "mapa+geo"),
    ("AHU",  "Ahuac",                    "capital_distrital",     "Chupaca",    -12.0983, -75.3103, "mapa+geo"),
    ("CHB",  "Chongos Bajo",             "capital_distrital",     "Chupaca",    -12.0989, -75.2758, "mapa+geo"),
    ("HMCH", "Huamancaca Chico",         "capital_distrital",     "Chupaca",    -12.0625, -75.2531, "mapa+geo"),
    ("HUAC", "Huáchac",                  "capital_distrital",     "Chupaca",    -12.0261, -75.3222, "mapa+geo"),
    ("YCS",  "Ycsos",                    "poblado",               "Chupaca",    -12.0850, -75.2950, "estimada"),
    ("PIL",  "Pilcomayo",                "capital_distrital",     "Chupaca",    -12.0264, -75.2861, "mapa+geo"),
    ("SIC",  "Sicaya",                   "capital_distrital",     "Chupaca",    -12.0339, -75.3097, "mapa+geo"),

    ("CON",  "Concepción",               "capital_provincial",    "Concepción", -11.9186, -75.3167, "mapa+geo"),
    ("SDP",  "Santo Domingo del Prado",  "poblado",               "Concepción", -11.9067, -75.3178, "estimada"),
    ("MAT",  "Matahuasi",                "capital_distrital",     "Concepción", -11.8869, -75.3247, "mapa+geo"),
    ("SIN",  "Sincos",                   "capital_distrital",     "Concepción", -11.8794, -75.3767, "mapa+geo"),
    ("QUI2", "Quichuay",                 "capital_distrital",     "Concepción", -11.8908, -75.2914, "estimada"),
    ("SRO",  "Santa Rosa de Ocopa",      "poblado",               "Concepción", -11.8992, -75.3011, "mapa+geo"),
    ("ING",  "Ingenio",                  "capital_distrital",     "Concepción", -11.8794, -75.2589, "mapa+geo"),
    ("ORC",  "Orcotuna",                 "capital_distrital",     "Concepción", -11.9414, -75.3358, "mapa+geo"),
    ("MIT",  "Mito",                     "capital_distrital",     "Concepción", -11.9433, -75.3706, "mapa+geo"),
    ("ACO",  "Aco",                      "capital_distrital",     "Concepción", -11.9078, -75.3939, "mapa+geo"),
    ("CHAM", "Chambara",                 "capital_distrital",     "Concepción", -11.9506, -75.4133, "estimada"),
    ("SMIG", "San Miguel",               "poblado",               "Concepción", -11.9611, -75.3961, "estimada"),
    ("SAY",  "Sayán",                    "poblado",               "Concepción", -11.9944, -75.4381, "estimada"),
    ("HUAN", "Huanchar",                 "poblado",               "Concepción", -11.8608, -75.3172, "estimada"),
]

COORDS = {n[0]: (n[4], n[5]) for n in NODOS}
NOMBRES = {n[0]: n[1] for n in NODOS}
TIPOS = {n[0]: n[2] for n in NODOS}
PROVINCIAS = {n[0]: n[3] for n in NODOS}

# 2. LOGISTICA (inventario y recursos por nodo)
LOGISTICA = {

"HYO": {
    "agua": 3000,
    "alimentos": 4200,
    "primeros_auxilios": 1200,
    "vehiculos": {"camion_5T": 8, "camion_2T": 5, "camioneta_4x4": 10, "ambulancia": 6, "helicoptero": 1},
    "hospitales": 2,
    "centros_salud": 18,
},
"ETB": {
    "agua": 1200, "alimentos": 1500, "primeros_auxilios": 450,
    "vehiculos": {"camion_5T": 2, "camion_2T": 2, "camioneta_4x4": 3},
    "hospitales": 1, "centros_salud": 5,
},
"CHI": {
    "agua": 1000, "alimentos": 1200, "primeros_auxilios": 350,
    "vehiculos": {"camion_2T": 2, "camioneta_4x4": 2},
    "hospitales": 0, "centros_salud": 4,
},
"HCN": {
    "agua": 350, "alimentos": 420, "primeros_auxilios": 120,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 1,
},
"HYC": {
    "agua": 300, "alimentos": 380, "primeros_auxilios": 100,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 1,
},
"VIQ": {
    "agua": 220, "alimentos": 260, "primeros_auxilios": 80,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"HCP": {
    "agua": 180, "alimentos": 200, "primeros_auxilios": 60,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"CHU_P": {
    "agua": 180, "alimentos": 210, "primeros_auxilios": 60,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"SAP": {
    "agua": 700, "alimentos": 850, "primeros_auxilios": 250,
    "vehiculos": {"camion_2T": 1, "camioneta_4x4": 2},
    "hospitales": 0, "centros_salud": 3,
},
"PUC": {
    "agua": 260, "alimentos": 320, "primeros_auxilios": 90,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"3DIC": {
    "agua": 150, "alimentos": 170, "primeros_auxilios": 50,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"PAC": {
    "agua": 100, "alimentos": 120, "primeros_auxilios": 40,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"HCOL": {
    "agua": 100, "alimentos": 120, "primeros_auxilios": 40,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"COCH": {
    "agua": 220, "alimentos": 260, "primeros_auxilios": 70,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"QUIL": {
    "agua": 600, "alimentos": 700, "primeros_auxilios": 200,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"SANO": {
    "agua": 250, "alimentos": 300, "primeros_auxilios": 80,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"HUAL": {
    "agua": 420, "alimentos": 500, "primeros_auxilios": 130,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 2,
},
"SAGU": {
    "agua": 320, "alimentos": 360, "primeros_auxilios": 90,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"SJT": {
    "agua": 520, "alimentos": 650, "primeros_auxilios": 180,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"CHP": {
    "agua": 1500, "alimentos": 2000, "primeros_auxilios": 650,
    "vehiculos": {"camion_5T": 3, "camion_2T": 2, "camioneta_4x4": 4, "ambulancia": 2},
    "hospitales": 0, "centros_salud": 6,
},
"AHU": {
    "agua": 420, "alimentos": 500, "primeros_auxilios": 140,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 1,
},
"CHB": {
    "agua": 300, "alimentos": 380, "primeros_auxilios": 100,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"HMCH": {
    "agua": 520, "alimentos": 650, "primeros_auxilios": 180,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"HUAC": {
    "agua": 350, "alimentos": 420, "primeros_auxilios": 120,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"YCS": {
    "agua": 120, "alimentos": 140, "primeros_auxilios": 40,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"PIL": {
    "agua": 650, "alimentos": 820, "primeros_auxilios": 240,
    "vehiculos": {"camion_2T": 1, "camioneta_4x4": 2},
    "hospitales": 0, "centros_salud": 2,
},
"SIC": {
    "agua": 900, "alimentos": 1100, "primeros_auxilios": 320,
    "vehiculos": {"camion_5T": 1, "camioneta_4x4": 2},
    "hospitales": 0, "centros_salud": 3,
},
"CON": {
    "agua": 1800, "alimentos": 2300, "primeros_auxilios": 700,
    "vehiculos": {"camion_5T": 2, "camion_2T": 2, "camioneta_4x4": 4, "ambulancia": 2},
    "hospitales": 0, "centros_salud": 5,
},

# --- localidades de la provincia de Concepción ---
"SDP": {
    "agua": 130, "alimentos": 150, "primeros_auxilios": 45,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"MAT": {
    "agua": 550, "alimentos": 680, "primeros_auxilios": 190,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"SIN": {
    "agua": 480, "alimentos": 580, "primeros_auxilios": 160,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"QUI2": {
    "agua": 220, "alimentos": 260, "primeros_auxilios": 70,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"SRO": {
    "agua": 200, "alimentos": 240, "primeros_auxilios": 65,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"ING": {
    "agua": 260, "alimentos": 310, "primeros_auxilios": 85,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"ORC": {
    "agua": 420, "alimentos": 500, "primeros_auxilios": 140,
    "vehiculos": {"camioneta_4x4": 1},
    "hospitales": 0, "centros_salud": 2,
},
"MIT": {
    "agua": 300, "alimentos": 360, "primeros_auxilios": 100,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"ACO": {
    "agua": 200, "alimentos": 240, "primeros_auxilios": 65,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"CHAM": {
    "agua": 180, "alimentos": 210, "primeros_auxilios": 55,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 1,
},
"SMIG": {
    "agua": 140, "alimentos": 160, "primeros_auxilios": 45,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"SAY": {
    "agua": 120, "alimentos": 140, "primeros_auxilios": 40,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
"HUAN": {
    "agua": 110, "alimentos": 130, "primeros_auxilios": 40,
    "vehiculos": {},
    "hospitales": 0, "centros_salud": 0,
},
}

_faltantes = [n[0] for n in NODOS if n[0] not in LOGISTICA]
if _faltantes:
    raise ValueError(f"Nodos sin datos de logística: {_faltantes}")

# 3. ARISTAS / RED VIAL
ARISTAS_BASE = [
    # (origen, destino, estado, km_mapa_o_None)
    ("HYO", "ETB", "asfaltada", 2.0),
    ("ETB", "PIL", "asfaltada", 4.2),
    ("PIL", "CHP", "asfaltada", 4.6),
    ("ETB", "QUIL", "asfaltada", 17.0),
    ("QUIL", "SJT", "asfaltada", 8.0),
    ("SJT", "CON", "asfaltada", 24.0),
    ("CON", "MIT", "asfaltada", 26.0),
    ("CON", "SDP", "asfaltada", 29.0),
    ("SDP", "MAT", "asfaltada", 2.9),
    ("MAT", "SIN", "asfaltada", 19.0),
    ("CON", "SRO", "sin_asfaltar", 6.4),
    ("SRO", "QUI2", "sin_asfaltar", 1.6),
    ("QUI2", "ING", "sin_asfaltar", 2.3),
    ("SJT", "SANO", "sin_asfaltar", 5.4),
    ("SANO", "HUAL", "sin_asfaltar", 10.0),
    ("HUAL", "SAGU", "sin_asfaltar", 6.0),
    ("SAGU", "COCH", "trocha", 5.6),
    ("MIT", "ORC", "asfaltada", 5.9),
    ("ORC", "CHAM", "sin_asfaltar", 12.0),
    ("CHAM", "SMIG", "sin_asfaltar", 2.20),
    ("MIT", "ACO", "sin_asfaltar", 6.6),
    ("CHAM", "SAY", "trocha", 5.56),
    ("CON", "HUAN", "sin_asfaltar", 6.43),
    ("CHP", "AHU", "sin_asfaltar", 4.14),
    ("AHU", "YCS", "sin_asfaltar", 2.22),
    ("YCS", "CHB", "sin_asfaltar", 2.61),
    ("CHB", "HUAC", "sin_asfaltar", 9.42),
    ("HUAC", "SIC", "sin_asfaltar", 1.62),
    ("SIC", "PIL", "sin_asfaltar", 2.70),
    ("CHP", "HMCH", "sin_asfaltar", 3.97),
    ("HMCH", "3DIC", "trocha", 6.89),
    ("3DIC", "PAC", "trocha", 1.13),
    ("PAC", "HYC", "trocha", 3.93),
    ("HYO", "CHI", "asfaltada", 1.70),
    ("CHI", "HCN", "asfaltada", 1.35),
    ("HCN", "HCOL", "sin_asfaltar", 1.93),
    ("HCN", "SAP", "asfaltada", 2.25),
    ("SAP", "PUC", "asfaltada", 5.76),
    ("HYO", "HYC", "asfaltada", 5.43),
    ("HYC", "VIQ", "asfaltada", 3.20),
    ("VIQ", "HCP", "sin_asfaltar", 2.10),
    ("VIQ", "CHU_P", "sin_asfaltar", 1.84),
    ("CHU_P", "PUC", "sin_asfaltar", 11.12),
]


def _haversine(a, b):
    """Distancia en línea recta (km) entre dos puntos (lat, lon)."""
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _construir_aristas():
    aristas = []
    for o, d, estado, km in ARISTAS_BASE:
        if km is not None:
            dist, fuente = km, "mapa"
        else:
            dist = round(_haversine(COORDS[o], COORDS[d]) * 1.25, 2)
            fuente = "haversine_est(+25%)"
        aristas.append({
            "origen": o, "origen_nombre": NOMBRES[o],
            "destino": d, "destino_nombre": NOMBRES[d],
            "estado_via": estado,
            "distancia_km": dist,
            "fuente_distancia": fuente,
        })
    return aristas


ARISTAS = _construir_aristas()


def _construir_adyacencia():
    """Lista de adyacencia no dirigida: {nodo: [(vecino, distancia_km, estado_via), ...]}"""
    adj = {n[0]: [] for n in NODOS}
    for a in ARISTAS:
        adj[a["origen"]].append((a["destino"], a["distancia_km"], a["estado_via"]))
        adj[a["destino"]].append((a["origen"], a["distancia_km"], a["estado_via"]))
    return adj


ADYACENCIA = _construir_adyacencia()


def ruta_mas_corta(origen_id, destino_id, evitar_trocha=False):
    """Dijkstra clásico sobre ADYACENCIA, ponderado por distancia_km.
    Sirve como línea base (óptimo conocido) contra la cual comparar el
    resultado de un solver cuántico (QAOA / quantum annealing) sobre el
    mismo grafo. Si evitar_trocha=True, penaliza fuertemente los tramos
    en trocha (para simular que un camión pesado no puede usarlos).
    Devuelve (lista_de_ids_del_camino, distancia_total_km).
    """
    import heapq
    PENALIZACION_TROCHA = 1000  # km "virtuales" para desincentivar trochas
    dist = {n[0]: math.inf for n in NODOS}
    prev = {}
    dist[origen_id] = 0.0
    pq = [(0.0, origen_id)]
    visitados = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in visitados:
            continue
        visitados.add(u)
        if u == destino_id:
            break
        for v, km, estado in ADYACENCIA[u]:
            peso = km + (PENALIZACION_TROCHA if (evitar_trocha and estado == "trocha") else 0)
            nd = d + peso
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if destino_id != origen_id and destino_id not in prev:
        return None, math.inf
    camino = [destino_id]
    while camino[-1] != origen_id:
        camino.append(prev[camino[-1]])
    camino.reverse()
    return camino, round(dist[destino_id], 2)

# 4. HOSPITALES / ESTABLECIMIENTOS DE SALUD 
HOSPITALES = [
    {"id": "H1",  "nombre": "Hospital Regional Docente Clínico Quirúrgico Daniel A. Carrión",
     "nodo_id": "HYO", "ubicacion": "Huancayo", "red": "MINSA", "categoria": "III-1",
     "lat": -12.0700, "lon": -75.2100, "direccion": "Av. Daniel Alcides Carrión N° 1556, Huancayo"},
    {"id": "H2",  "nombre": "Hospital Nacional Ramiro Prialé Prialé",
     "nodo_id": "ETB", "ubicacion": "El Tambo (Huancayo)", "red": "EsSalud", "categoria": "III-1",
     "lat": -12.0500, "lon": -75.2200, "direccion": "El Tambo, Huancayo"},
    {"id": "H3",  "nombre": "Hospital El Carmen",
     "nodo_id": "HYO", "ubicacion": "Huancayo", "red": "Gob. Regional Junín", "categoria": "II-2",
     "lat": -12.0680, "lon": -75.2080, "direccion": "Jr. Puno N° 911, Huancayo"},
    {"id": "H4",  "nombre": "Dirección Red de Salud Chupaca (sede administrativa)",
     "nodo_id": "ETB", "ubicacion": "El Tambo", "red": "MINSA", "categoria": "Red de Salud",
     "lat": -12.0500, "lon": -75.2210, "direccion": "Jr. Julio C. Tello N° 488, El Tambo"},
    {"id": "H5",  "nombre": "Centro de Salud Pedro Sánchez Meza",
     "nodo_id": "CHP", "ubicacion": "Chupaca", "red": "MINSA", "categoria": "I-4",
     "lat": -12.0672, "lon": -75.2892, "direccion": "Chupaca"},
    {"id": "H6",  "nombre": "Centro de Salud Chongos Bajo",
     "nodo_id": "CHB", "ubicacion": "Chongos Bajo", "red": "MINSA", "categoria": "I-3",
     "lat": -12.0989, "lon": -75.2758, "direccion": "Chongos Bajo"},
    {"id": "H7",  "nombre": "Centro de Salud Huáchac",
     "nodo_id": "HUAC", "ubicacion": "Huáchac", "red": "MINSA", "categoria": "I-3",
     "lat": -12.0261, "lon": -75.3222, "direccion": "Huáchac"},
    {"id": "H8",  "nombre": "Centro de Salud Mental Ahuac",
     "nodo_id": "AHU", "ubicacion": "Ahuac", "red": "MINSA", "categoria": "I-2",
     "lat": -12.0983, "lon": -75.3103, "direccion": "Ahuac"},
    {"id": "H9",  "nombre": "Puesto de Salud Ahuac",
     "nodo_id": "AHU", "ubicacion": "Ahuac", "red": "MINSA", "categoria": "I-1",
     "lat": -12.0983, "lon": -75.3103, "direccion": "Ahuac"},
    {"id": "H10", "nombre": "Puesto de Salud Tres de Diciembre",
     "nodo_id": "3DIC", "ubicacion": "3 de Diciembre", "red": "MINSA", "categoria": "I-1",
     "lat": -12.1244, "lon": -75.2517, "direccion": "3 de Diciembre"},
    {"id": "H11", "nombre": "Puesto de Salud Huamancaca Chico",
     "nodo_id": "HMCH", "ubicacion": "Huamancaca Chico", "red": "MINSA", "categoria": "I-1",
     "lat": -12.0625, "lon": -75.2531, "direccion": "Huamancaca Chico"},
]

# 5. PRIORIDAD DE COMUNIDADES (escenario sismo, epicentro ~Chupaca)
COMUNIDADES = [
    "CHP", "AHU", "CHB", "HMCH", "HUAC", "YCS", "PIL", "SIC", "3DIC", "PAC", "HCOL",
    "HYC", "VIQ", "HCP", "CHU_P", "SAP", "PUC", "CHI", "HCN", "ETB", "HYO",
    "CON", "ORC", "MIT", "ACO", "CHAM", "SMIG", "SAY", "SIN", "MAT", "SJT",
    "QUIL", "SANO", "HUAL", "SAGU", "COCH", "SRO", "QUI2", "ING", "SDP", "HUAN",
]


EPICENTRO_ID = "CHP"

def construir_prioridad(epicentro_id=EPICENTRO_ID):
    """Recalcula el ranking de urgencia asumiendo el epicentro en
    `epicentro_id` (debe ser un id presente en NODOS). Útil para comparar
    escenarios: construir_prioridad("CHP") vs construir_prioridad("CHB").
    """
    epicentro = COORDS[epicentro_id]
    tiene_salud = {h["nodo_id"] for h in HOSPITALES}
    estado_via_nodo = {}
    for a in ARISTAS:
        estado_via_nodo.setdefault(a["origen"], set()).add(a["estado_via"])
        estado_via_nodo.setdefault(a["destino"], set()).add(a["estado_via"])

    filas = []
    for cid in COMUNIDADES:
        dist_epi = round(_haversine(COORDS[cid], epicentro), 2)
        vias = estado_via_nodo.get(cid, {"desconocida"})
        aislado = "trocha" in vias or "sin_asfaltar" in vias
        salud_propia = cid in tiene_salud
        score = 0.0
        score += max(0, 20 - dist_epi) * 2
        score += 0 if salud_propia else 15
        score += 10 if aislado else 0
        filas.append({
            "id": cid, "nombre": NOMBRES[cid],
            "dist_km_epicentro": dist_epi,
            "tiene_salud_propia": salud_propia,
            "acceso_dificil": aislado,
            "score_prioridad": round(score, 1),
        })

    filas.sort(key=lambda r: -r["score_prioridad"])
    for i, fila in enumerate(filas, start=1):
        fila["ranking"] = i
    return filas


EPICENTRO = COORDS[EPICENTRO_ID]
PRIORIDAD_COMUNIDADES = construir_prioridad(EPICENTRO_ID)

# 6. VISTA CONSOLIDADA POR NODO (input directo para el optimizador)
def _construir_nodos_info():
    prioridad_por_id = {f["id"]: f for f in PRIORIDAD_COMUNIDADES}
    info = {}
    for n in NODOS:
        nid = n[0]
        info[nid] = {
            "nombre": n[1],
            "tipo": n[2],
            "provincia": n[3],
            "lat": n[4],
            "lon": n[5],
            "fuente_coord": n[6],
            "recursos": LOGISTICA[nid],
            "prioridad": prioridad_por_id.get(nid),
        }
    return info


NODOS_INFO = _construir_nodos_info()

# 7. FLOTA TOTAL DISPONIBLE (para el problema de asignación de vehículos)
def _resumen_flota():
    total = {}
    for datos in LOGISTICA.values():
        for tipo, cant in datos["vehiculos"].items():
            total[tipo] = total.get(tipo, 0) + cant
    return total


FLOTA_TOTAL = _resumen_flota()

# 8. GRAFO (opcional, requiere `pip install networkx`)
def construir_grafo():
    """Devuelve un networkx.Graph con nodos y aristas listos para
    optimización clásica o cuántica de rutas. Requiere `networkx`.
    """
    import networkx as nx

    G = nx.Graph()
    for nid, data in NODOS_INFO.items():
        G.add_node(nid, **data)
    for a in ARISTAS:
        G.add_edge(a["origen"], a["destino"],
                   distancia_km=a["distancia_km"],
                   estado_via=a["estado_via"])
    return G


if __name__ == "__main__":
    print(f"Nodos: {len(NODOS)}")
    print(f"Aristas: {len(ARISTAS)}")
    print(f"Hospitales: {len(HOSPITALES)}")
    print(f"Comunidades priorizadas: {len(PRIORIDAD_COMUNIDADES)}")
    print(f"Flota total: {FLOTA_TOTAL}")
    print("Top 5 prioridad:")
    for fila in PRIORIDAD_COMUNIDADES[:5]:
        print(" ", fila)
