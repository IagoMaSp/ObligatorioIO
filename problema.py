import mip
from mip import BINARY, Model, maximize, xsum, OptimizationStatus

# DATOS

# Cirugías: (id, nombre, slots_operacion, slots_limpieza, contaminada, prioridad)
cirugias_raw= [
    (1,  "Cateterización venosa central compleja",  1,  1, 0, 2),
    (2,  "Cateterización venosa central compleja",  1,  1, 0, 2),
    (3,  "Apendicectomía",                          2,  1, 0, 4),
    (4,  "Apendicectomía laparoscópica",            2,  1, 0, 4),
    (5,  "Hernia inguinal",                         2,  1, 0, 3),
    (6,  "Hernia inguinal",                         2,  1, 0, 3),
    (7,  "Hernia umbilical",                        2,  1, 0, 3),
    (8,  "Colecistectomía laparoscópica",           2,  1, 0, 4),
    (9,  "Apendicectomía (paciente KPC+)",          2,  2, 1, 4),
    (10, "Hernia inguinal (paciente NDM+)",         2,  2, 1, 3),
    (11, "Puente arterial femoropoplíteo",          10, 1, 0, 5),
    (12, "Puente arterial femoropoplíteo",          10, 1, 0, 5),
    (13, "Endarterectomía carotídea",               8,  1, 0, 5),
    (14, "Aneurisma aórtico abdominal",             12, 1, 0, 5),
    (15, "Reconstrucción vascular compleja",        10, 1, 0, 5),
    (16, "Neurocirugía (tumor)",                    20, 1, 0, 5),
    (17, "Linfadenectomía retroperitoneal",         20, 1, 0, 5),
    (18, "Cirugía retroperitoneal compleja",        19, 1, 0, 5),
]

I   = [r[0] for r in cirugias_raw]
nom = {r[0]: r[1] for r in cirugias_raw}
d   = {r[0]: r[2] for r in cirugias_raw}   # Bloques operación
l   = {r[0]: r[3] for r in cirugias_raw}   # Bloques limpieza
cont= {r[0]: r[4] for r in cirugias_raw}   # Contaminada
p   = {r[0]: r[5] for r in cirugias_raw}   # Prioridad

dur = {i: d[i] + l[i] for i in I}          # Duración total ocupando el quirófano

Q = list(range(1, 7))    # 6 Quirófanos
T = list(range(1, 25))   # 24 Bloques de 30 min
T_MAX = 24

# Cirujanos: (id, nombre, especialidad)
cirujanos_raw = [
    ("C1", "Dra. Pérez",     "Cirugía General"),
    ("C2", "Dr. Martínez",   "Cirugía General"),
    ("C3", "Dr. Fernández",  "Cirugía General"),
    ("C4", "Dra. Silva",     "Cirugía Vascular"),
    ("C5", "Dra. Rodríguez", "Neurocirugía"),
    ("C6", "Dra. Díaz",      "Cirugía Oncológica"),
]
C        = [r[0] for r in cirujanos_raw]
nom_cir  = {r[0]: r[1] for r in cirujanos_raw}
esp_cir  = {r[0]: r[2] for r in cirujanos_raw}

# Especialidad requerida por cada cirugía
esp_req = {
    1:  "Cirugía General",   2:  "Cirugía General",
    3:  "Cirugía General",   4:  "Cirugía General",
    5:  "Cirugía General",   6:  "Cirugía General",
    7:  "Cirugía General",   8:  "Cirugía General",
    9:  "Cirugía General",   10: "Cirugía General",
    11: "Cirugía Vascular",  12: "Cirugía Vascular",
    13: "Cirugía Vascular",  14: "Cirugía Vascular",
    15: "Cirugía Vascular",  16: "Neurocirugía",
    17: "Cirugía Oncológica",18: "Cirugía Oncológica",
}

# Hab[i,c] = 1 si el cirujano c tiene la especialidad requerida para i
Hab = {
    (i, c): 1 if esp_cir[c] == esp_req[i] else 0
    for i in I for c in C
}

# OPTIMIZACIÓN 1: precalcular, para cada cirugía, la lista de cirujanos
# habilitados. Esto evita iterar luego sobre cirujanos no habilitados
Cirujanos_validos = {i: [c for c in C if Hab[(i, c)] == 1] for i in I}

# Personal de soporte — capacidades globales por Bloque (constantes)
R   = ["anestesistas_g2", "circulantes", "instrumentistas", "camas_preanest"]
Cap = {
    "anestesistas_g2":  6,
    "circulantes":      7,
    "instrumentistas":  8,
    "camas_preanest":   4,
}
req = {}
for i in I:
    req[(i, "anestesistas_g2")]  = 1
    req[(i, "circulantes")]      = 2 if cont[i] else 1
    req[(i, "instrumentistas")]  = 2 if p[i] >= 5 else 1
    req[(i, "camas_preanest")]   = 1


# MODELO

m = Model("HospitalMaciel", solver_name=mip.CBC)
m.verbose    = 1
m.max_seconds = 60   # Tiempo máximo 5 minutos
m.max_mip_gap = 0.01  # Gap de optimalidad 1%

# VARIABLES

# OPTIMIZACIÓN 2: x[i][q][t] solo se crea para los t en los que la cirugía
# realmente cabe en la jornada (t <= T_MAX - dur[i] + 1). Esto reemplaza la
# antigua Restricción 2 (que fijaba esas variables en 0 a posteriori) por
# directamente no crearlas: menos variables y menos restricciones.
x = {
    (i, q, t): m.add_var(var_type=BINARY, name=f"x_{i}_{q}_{t}")
    for i in I for q in Q for t in T
    if t <= T_MAX - dur[i] + 1
}

def x_get(i, q, t):
    """Devuelve la variable x si existe, o 0 si fue podada por ventana de tiempo."""
    return x[(i, q, t)] if (i, q, t) in x else 0

# y[i][c] — asignación de cirujano (solo para cirujanos habilitados)
y = {
    (i, c): m.add_var(var_type=BINARY, name=f"y_{i}_{c}")
    for i in I for c in Cirujanos_validos[i]
}

def y_get(i, c):
    return y[(i, c)] if (i, c) in y else 0

# Activa[i][t] — etapa operativa (parte de "operación", sin limpieza)
Activa = {
    (i, t): m.add_var(var_type=BINARY, name=f"act_{i}_{t}")
    for i in I for t in T
}

# inicio[i] — slot de inicio de la cirugía i (0 si no se programa, ver R2b)
inicio = {
    i: xsum(t * x_get(i, q, t) for q in Q for t in T)
    for i in I
}

# prog[i] — 1 si la cirugía i fue programada (en algún quirófano/slot)
prog = {
    i: xsum(x_get(i, q, t) for q in Q for t in T)
    for i in I
}

# fin[i] — slot final (operación + limpieza) ocupado por la cirugía i
fin = {
    i: inicio[i] + (dur[i] - 1) * prog[i]
    for i in I
}

# orden[i,j] — variable de precedencia para pares de cirugías que podrían
# compartir cirujano (ver Restricción 7 simplificada). Solo se crea para
# pares que comparten al menos un cirujano habilitado: si dos cirugías no
# pueden compartir cirujano nunca hace falta la variable de orden.
pares_con_cirujano_comun = []
for idx, i in enumerate(I):
    for j in I[idx + 1:]:
        if set(Cirujanos_validos[i]) & set(Cirujanos_validos[j]):
            pares_con_cirujano_comun.append((i, j))

orden = {
    (i, j): m.add_var(var_type=BINARY, name=f"orden_{i}_{j}")
    for (i, j) in pares_con_cirujano_comun
}

# FUNCIÓN OBJETIVO
m.objective = maximize(
    xsum(p[i] * x_get(i, q, t) for i in I for q in Q for t in T if (i, q, t) in x)
)

# RESTRICCIONES

# Restricción 1 — Unicidad: cada cirugía se programa a lo sumo una vez
for i in I:
    m += prog[i] <= 1

# (La antigua Restricción 2 de ventana de tiempo ya no hace falta:
#  las variables x[i,q,t] fuera de ventana directamente no se crean.)

# Restricción 3 — No superposición en quirófanos (un quirófano, una cirugía
# activa -incluida limpieza- por bloque)
for q in Q:
    for t in T:
        terms = [
            x_get(i, q, tau)
            for i in I
            for tau in range(max(1, t - dur[i] + 1), t + 1)
            if tau in T and (i, q, tau) in x
        ]
        if terms:
            m += xsum(terms) <= 1

# Restricción 3b — Cirugía contaminada ocupa el quirófano en exclusiva
# durante toda la jornada
for i in I:
    if cont[i]:
        for q in Q:
            for j in I:
                if j != i:
                    m += (
                        xsum(x_get(j, q, t) for t in T if (j, q, t) in x) +
                        xsum(x_get(i, q, t) for t in T if (i, q, t) in x)
                    ) <= 1

# Restricción 4 — Definición de Activa[i,t]
for i in I:
    for t in T:
        ventana = [
            x_get(i, q, tau)
            for q in Q
            for tau in range(max(1, t - d[i] + 1), t + 1)
            if tau in T and (i, q, tau) in x
        ]
        if ventana:
            expr = xsum(ventana)
            m += Activa[(i, t)] <= expr           # si nadie arrancó, no puede estar activa
            m += Activa[(i, t)] >= expr / len(Q)  # si alguien arrancó, debe estar activa
        else:
            m += Activa[(i, t)] == 0

# Restricción 5 — Obligatoriedad de cirujano: exactamente uno si la cirugía
# está programada
for i in I:
    m += xsum(y_get(i, c) for c in Cirujanos_validos[i]) == prog[i]

# (La antigua Restricción 6 de compatibilidad de especialidad ya no hace
#  falta: y[i,c] solo se crea para cirujanos habilitados, así que la
#  compatibilidad queda garantizada por construcción.)

# Restricción 7 — Disponibilidad del cirujano (no-solape), reformulada con
# variables de orden + big-M en lugar de iterar sobre los 24 slots por cada
# par de cirugías y cada cirujano. Solo se generan para pares que comparten
# al menos un cirujano habilitado (pares_con_cirujano_comun).
BIG_M = T_MAX  # cota válida: ningún inicio/fin excede T_MAX

for (i, j) in pares_con_cirujano_comun:
    cirujanos_comunes = set(Cirujanos_validos[i]) & set(Cirujanos_validos[j])
    # Si i y j comparten el cirujano c, entonces y[i,c] + y[j,c] = 2 y
    # holgura_c = 0, forzando que una preceda a la otra (sin solape). Si no
    # comparten ese cirujano específico, holgura_c >= 1 y la restricción
    # correspondiente queda relajada (inactiva). Una restricción de orden
    # por cirujano común es suficiente y se mantiene lineal.
    for c in cirujanos_comunes:
        holgura_c = 2 - y_get(i, c) - y_get(j, c)
        m += inicio[i] - fin[j] >= 1 - BIG_M * (1 - orden[(i, j)]) - BIG_M * holgura_c
        m += inicio[j] - fin[i] >= 1 - BIG_M * orden[(i, j)] - BIG_M * holgura_c

# Restricción 8 — Capacidad de personal de soporte por bloque
for r in R:
    for t in T:
        m += xsum(req[(i, r)] * Activa[(i, t)] for i in I) <= Cap[r]


# OPTIMIZACION
print("\n" + "="*60)
print("Resolviendo con CBC (python-mip)...")
print(f"Variables: {m.num_cols}  |  Restricciones: {m.num_rows}")
print("="*60 + "\n")

status = m.optimize()

# RESULTADOS
def slot_a_hora(t):
    mins = (t - 1) * 30
    return f"{8 + mins // 60:02d}:{mins % 60:02d}"

print("\n" + "="*70)
print("SOLUCIÓN — PROGRAMACIÓN BLOQUE QUIRÚRGICO HOSPITAL MACIEL")
print("="*70)

if status in (OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE):
    print(f"\nValor objetivo (prioridad acumulada) : {m.objective_value:.1f}")
    print(f"Gap MIP                               : {m.gap*100:.2f}%\n")

    programadas = []
    for i in I:
        for q in Q:
            for t in T:
                if (i, q, t) in x and x[(i, q, t)].x > 0.5:
                    cir_asig = next((c for c in Cirujanos_validos[i] if y[(i, c)].x > 0.5), "—")
                    programadas.append({
                        "id":      i,
                        "nombre":  nom[i],
                        "q":       q,
                        "inicio":  t,
                        "fin_op":  t + d[i] - 1,
                        "fin_lim": t + d[i] + l[i] - 1,
                        "cir":     nom_cir.get(cir_asig, cir_asig),
                        "prio":    p[i],
                        "cont":    "Sí" if cont[i] else "No",
                    })

    programadas.sort(key=lambda r: (r["q"], r["inicio"]))

    header = (f"{'ID':>3}  {'Quiróf':>6}  {'Inicio':>6}  {'Fin Op':>6}  "
              f"{'Fin Lim':>7}  {'P':>2}  {'Cont':>4}  {'Cirujano':<22}  Cirugía")
    print(header)
    print("-" * len(header))
    for r in programadas:
        print(
            f"{r['id']:>3}  "
            f"Q{r['q']:>5}  "
            f"{slot_a_hora(r['inicio']):>6}  "
            f"{slot_a_hora(r['fin_op']):>6}  "
            f"{slot_a_hora(r['fin_lim']):>7}  "
            f"{r['prio']:>2}  "
            f"{r['cont']:>4}  "
            f"{r['cir']:<22}  "
            f"{r['nombre']}"
        )

    print(f"\nCirugías programadas: {len(programadas)} / {len(I)}")

    print("\n── Utilización por quirófano ──")
    for q in Q:
        sub = [r for r in programadas if r["q"] == q]
        slots = sum(d[r["id"]] + l[r["id"]] for r in sub)
        print(f"  Q{q}: {len(sub)} cirugía(s)  —  {slots}/24 slots  ({slots/24*100:.0f}%)")

else:
    print(f"No se encontró solución factible. Status: {status}")