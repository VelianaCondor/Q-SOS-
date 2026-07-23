# **Q-SOS**
Proyecto desarrollado que busca desarrollar un modelo de detección de rutas óptimas en caso de desastres naturales basado en algoritmos cuánticos de priorización de recursos, vehículos, alimentos y medicamentos

---

# Instalación

1. Clona el repositorio:

```bash
https://github.com/VelianaCondor/Q-SOS-.git
cd Q-SOS
```

2. Instala las dependencias:

```bash
pip install streamlit networkx dimod dwave-ocean-sdk matplotlib numpy
```

3. Ejecuta la aplicación:

```bash
streamlit run qsos_app.py
```
--- 

# Problema

Los desastres naturales, como los terremotos, generan daños en la infraestructura vial que dificultan el acceso a las zonas afectadas y retrasan la atención de la población damnificada. Además, los recursos de emergencia (ambulancias, camiones, helicópteros, entre otros) son limitados y su asignación suele realizarse de forma manual o con información incompleta, incrementando los tiempos de respuesta y reduciendo la eficiencia de las operaciones de ayuda humanitaria.
Como caso de estudio, este proyecto se enfoca en el **sismo ocurrido en el distrito de Chongos Bajo**, provincia de Chupaca, región Junín, Perú.

---

# Solución

Proponemos un sistema basado en **optimización cuántica** que utiliza:
- **QUBO** para modelar el problema de optimización.
- **QAOA** para encontrar una asignación eficiente de recursos de emergencia.

El sistema modela hospitales, comunidades afectadas y la red vial como un grafo para representar el escenario de emergencia. A partir de esta representación, asigna el recurso más adecuado (ambulancias, camiones, helicópteros, entre otros) según la disponibilidad y las condiciones de acceso, calcula rutas considerando carreteras transitables o bloqueadas, minimiza el tiempo total de respuesta y prioriza la atención de las comunidades con mayor nivel de afectación.

---

# Funcionamiento

El flujo del sistema es el siguiente:

1. **Modelado del escenario**
   - Se representa la red vial mediante un grafo.
   - Los nodos corresponden a localidades, hospitales y centros logísticos.
   - Las aristas representan carreteras con sus respectivas distancias y condiciones.

2. **Selección automática de depósitos**
   - Se identifican los centros logísticos más cercanos al epicentro utilizando rutas reales sobre la red vial.

3. **Construcción del modelo de optimización**
   - Cada variable representa la cantidad de vehículos de un determinado tipo enviados desde un depósito.
   - Se consideran restricciones de disponibilidad de vehículos y cobertura de la demanda.

4. **Optimización**
   - Se minimiza la distancia total recorrida.
   - Se garantiza que la demanda de la comunidad afectada sea cubierta utilizando los recursos disponibles.

---

# Optimización Cuántica

El problema se formula como un **Constrained Quadratic Model (CQM)**, el cual puede transformarse en un modelo **QUBO** para ser resuelto mediante algoritmos de optimización cuántica.

Actualmente el proyecto permite ejecutar:
- Solución exacta (Fuerza Bruta)
- Simulated Annealing (heurística clásica inspirada en computación cuántica)
- D-Wave Hybrid CQM Solver
- Preparado para algoritmos basados en **QAOA**

---

# Caso de Estudio

**Ubicación:** Chongos Bajo, Chupaca, Junín - Perú

Escenario considerado:
- Terremoto con epicentro en Chongos Bajo.
- Localidades cercanas funcionan como depósitos logísticos.
- Los recursos son enviados hacia la comunidad afectada utilizando la red vial disponible.
- El sistema considera la disponibilidad de vehículos y las condiciones de las carreteras.

---

# Estructura del Proyecto

```text
.
├── datos_recuperacion.py        # Base de datos de localidades, recursos y red vial
├── depositos_cercanos.py        # Selección automática de depósitos cercanos
├── escenario_demo_chb.py        # Modelo de optimización y ejecución del escenario
└── README.md
```

---

# Tecnologías

- Python
- D-Wave Ocean SDK
- dimod
- NetworkX
- Simulated Annealing
- Optimización Cuántica
- QUBO
- QAOA

