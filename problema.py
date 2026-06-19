import mip
from mip import BINARY, Model, maximize, xsum, OptimizationStatus

def obtener_datos_por_defecto():
    """Retorna los datos de cirugías y cirujanos por defecto para pruebas."""
    cirugias_raw = [
        # (id, nombre, bloques_operacion, bloques_limpieza, es_contaminada, prioridad, especialidad_requerida)
        (1,  "Cateterización venosa central compleja",  1,  1, 0, 2, "Cirugía General"),
        (2,  "Cateterización venosa central compleja",  1,  1, 0, 2, "Cirugía General"),
        (3,  "Apendicectomía",                          2,  1, 0, 4, "Cirugía General"),
        (4,  "Apendicectomía laparoscópica",            2,  1, 0, 4, "Cirugía General"),
        (5,  "Hernia inguinal",                         2,  1, 0, 3, "Cirugía General"),
        (6,  "Hernia inguinal",                         2,  1, 0, 3, "Cirugía General"),
        (7,  "Hernia umbilical",                        2,  1, 0, 3, "Cirugía General"),
        (8,  "Colecistectomía laparoscópica",           2,  1, 0, 4, "Cirugía General"),
        (9,  "Apendicectomía (paciente KPC+)",          2,  2, 1, 4, "Cirugía General"),
        (10, "Hernia inguinal (paciente NDM+)",         2,  2, 1, 3, "Cirugía General"),
        (11, "Puente arterial femoropoplíteo",          10, 1, 0, 5, "Cirugía Vascular"),
        (12, "Puente arterial femoropoplíteo",          10, 1, 0, 5, "Cirugía Vascular"),
        (13, "Endarterectomía carotídea",               8,  1, 0, 5, "Cirugía Vascular"),
        (14, "Aneurisma aórtico abdominal",             12, 1, 0, 5, "Cirugía Vascular"),
        (15, "Reconstrucción vascular compleja",        10, 1, 0, 5, "Cirugía Vascular"),
        (16, "Neurocirugía (tumor)",                    20, 1, 0, 5, "Neurocirugía"),
        (17, "Linfadenectomía retroperitoneal",         20, 1, 0, 5, "Cirugía Oncológica"),
        (18, "Cirugía retroperitoneal compleja",        19, 1, 0, 5, "Cirugía Oncológica"),
    ]

    cirujanos_raw = [
        # (id, nombre, especialidad)
        ("C1", "Dra. Pérez",     "Cirugía General"),
        ("C2", "Dr. Martínez",   "Cirugía General"),
        ("C3", "Dr. Fernández",  "Cirugía General"),
        ("C4", "Dra. Silva",     "Cirugía Vascular"),
        ("C5", "Dra. Rodríguez", "Neurocirugía"),
        ("C6", "Dra. Díaz",      "Cirugía Oncológica"),
    ]

    recursos_soporte = {
        "anestesistas_g2":  6,
        "circulantes":      7,
        "instrumentistas":  8,
        "camas_preanest":   4,
    }

    return cirugias_raw, cirujanos_raw, recursos_soporte

def optimizar_asignacion_quirofanos(datos_cirugias, datos_cirujanos, capacidad_soporte, num_quirofanos=6, max_bloques=24, max_seconds=60):
    """
    Ejecuta el modelo de optimización MIP para asignar cirugías a quirófanos.
    """
    # Desempaquetar datos de cirugías
    ids_cirugias = [r[0] for r in datos_cirugias]
    nombre_cirugia = {r[0]: r[1] for r in datos_cirugias}
    bloques_operacion = {r[0]: r[2] for r in datos_cirugias}
    bloques_limpieza = {r[0]: r[3] for r in datos_cirugias}
    es_contaminada = {r[0]: r[4] for r in datos_cirugias}
    prioridad_cirugia = {r[0]: r[5] for r in datos_cirugias}
    especialidad_requerida = {r[0]: r[6] for r in datos_cirugias}

    duracion_total = {i: bloques_operacion[i] + bloques_limpieza[i] for i in ids_cirugias}

    ids_quirofanos = list(range(1, num_quirofanos + 1))
    bloques_tiempo = list(range(1, max_bloques + 1))

    # Desempaquetar datos de cirujanos
    ids_cirujanos = [r[0] for r in datos_cirujanos]
    nombre_cirujano = {r[0]: r[1] for r in datos_cirujanos}
    especialidad_cirujano = {r[0]: r[2] for r in datos_cirujanos}

    # Habilitación de cirujanos por cirugía
    cirujano_habilitado = {
        (i, c): 1 if especialidad_cirujano[c] == especialidad_requerida[i] else 0
        for i in ids_cirugias for c in ids_cirujanos
    }

    cirujanos_validos_por_cirugia = {
        i: [c for c in ids_cirujanos if cirujano_habilitado[(i, c)] == 1]
        for i in ids_cirugias
    }

    roles_soporte = ["anestesistas_g2", "circulantes", "instrumentistas", "camas_preanest"]
    requerimiento_soporte = {}
    for i in ids_cirugias:
        requerimiento_soporte[(i, "anestesistas_g2")]  = 1
        requerimiento_soporte[(i, "circulantes")]      = 2 if es_contaminada[i] else 1
        requerimiento_soporte[(i, "instrumentistas")]  = 2 if prioridad_cirugia[i] >= 5 else 1
        requerimiento_soporte[(i, "camas_preanest")]   = 1

    # MODELO
    modelo = Model("HospitalMaciel", solver_name=mip.CBC)
    modelo.verbose = 0
    modelo.max_seconds = max_seconds
    modelo.max_mip_gap = 0.01

    # VARIABLES

    var_asignacion_inicio = {
        (i, q, t): modelo.add_var(var_type=BINARY, name=f"x_{i}_{q}_{t}")
        for i in ids_cirugias for q in ids_quirofanos for t in bloques_tiempo
        if t <= max_bloques - duracion_total[i] + 1
    }

    def x_get(i, q, t):
        return var_asignacion_inicio.get((i, q, t), 0)

    var_asignacion_cirujano = {
        (i, c): modelo.add_var(var_type=BINARY, name=f"y_{i}_{c}")
        for i in ids_cirugias for c in cirujanos_validos_por_cirugia[i]
    }

    def y_get(i, c):
        return var_asignacion_cirujano.get((i, c), 0)

    var_cirugia_activa_en_bloque = {
        (i, t): modelo.add_var(var_type=BINARY, name=f"act_{i}_{t}")
        for i in ids_cirugias for t in bloques_tiempo
    }

    var_bloque_inicio = {
        i: xsum(t * x_get(i, q, t) for q in ids_quirofanos for t in bloques_tiempo)
        for i in ids_cirugias
    }

    var_esta_programada = {
        i: xsum(x_get(i, q, t) for q in ids_quirofanos for t in bloques_tiempo)
        for i in ids_cirugias
    }

    var_bloque_fin_total = {
        i: var_bloque_inicio[i] + (duracion_total[i] - 1) * var_esta_programada[i]
        for i in ids_cirugias
    }

    pares_con_cirujano_comun = []
    for idx, i in enumerate(ids_cirugias):
        for j in ids_cirugias[idx + 1:]:
            if set(cirujanos_validos_por_cirugia[i]) & set(cirujanos_validos_por_cirugia[j]):
                pares_con_cirujano_comun.append((i, j))

    var_orden_precedencia = {
        (i, j): modelo.add_var(var_type=BINARY, name=f"orden_{i}_{j}")
        for (i, j) in pares_con_cirujano_comun
    }

    # FUNCIÓN OBJETIVO
    modelo.objective = maximize(
        xsum(prioridad_cirugia[i] * x_get(i, q, t) for i in ids_cirugias for q in ids_quirofanos for t in bloques_tiempo if (i, q, t) in var_asignacion_inicio)
    )

    # RESTRICCIONES

    # 1. Unicidad: cada cirugía se programa a lo sumo una vez
    for i in ids_cirugias:
        modelo += var_esta_programada[i] <= 1

    # 2. No superposición en quirófanos
    for q in ids_quirofanos:
        for t in bloques_tiempo:
            terminos = [
                x_get(i, q, tau)
                for i in ids_cirugias
                for tau in range(max(1, t - duracion_total[i] + 1), t + 1)
                if tau in bloques_tiempo and (i, q, tau) in var_asignacion_inicio
            ]
            if terminos:
                modelo += xsum(terminos) <= 1

    # 3. Lógica de Cirugía Contaminada
    # Si la cirugía i es contaminada y la j NO lo es, y ambas van al mismo quirófano,
    # entonces i NO puede iniciar antes de que j termine. Es decir, i debe ser la última.
    BIG_M_CONTAM = 50
    for q in ids_quirofanos:
        for i in ids_cirugias:
            if es_contaminada[i]:
                prog_i_q = xsum(x_get(i, q, t) for t in bloques_tiempo)
                inicio_i_q = xsum(t * x_get(i, q, t) for t in bloques_tiempo)
                for j in ids_cirugias:
                    if not es_contaminada[j]:
                        prog_j_q = xsum(x_get(j, q, t) for t in bloques_tiempo)
                        fin_j_q = xsum((t + duracion_total[j] - 1) * x_get(j, q, t) for t in bloques_tiempo)
                        modelo += inicio_i_q >= (fin_j_q + 1) - BIG_M_CONTAM * (2 - prog_i_q - prog_j_q)

    # 4. Definición de Activa (solo durante operación, no limpieza)
    for i in ids_cirugias:
        for t in bloques_tiempo:
            ventana = [
                x_get(i, q, tau)
                for q in ids_quirofanos
                for tau in range(max(1, t - bloques_operacion[i] + 1), t + 1)
                if tau in bloques_tiempo and (i, q, tau) in var_asignacion_inicio
            ]
            if ventana:
                expr = xsum(ventana)
                modelo += var_cirugia_activa_en_bloque[(i, t)] <= expr
                modelo += var_cirugia_activa_en_bloque[(i, t)] >= expr / num_quirofanos
            else:
                modelo += var_cirugia_activa_en_bloque[(i, t)] == 0

    # 5. Asignación de cirujano si se programa
    for i in ids_cirugias:
        if cirujanos_validos_por_cirugia[i]:
            modelo += xsum(y_get(i, c) for c in cirujanos_validos_por_cirugia[i]) == var_esta_programada[i]
        else:
            # Si no hay cirujanos válidos, no se puede programar
            modelo += var_esta_programada[i] == 0

    # 6. Disponibilidad del cirujano (no-solape)
    BIG_M = max_bloques
    for (i, j) in pares_con_cirujano_comun:
        cirujanos_comunes = set(cirujanos_validos_por_cirugia[i]) & set(cirujanos_validos_por_cirugia[j])
        for c in cirujanos_comunes:
            holgura_c = 2 - y_get(i, c) - y_get(j, c)
            modelo += var_bloque_inicio[i] - var_bloque_fin_total[j] >= 1 - BIG_M * (1 - var_orden_precedencia[(i, j)]) - BIG_M * holgura_c
            modelo += var_bloque_inicio[j] - var_bloque_fin_total[i] >= 1 - BIG_M * var_orden_precedencia[(i, j)] - BIG_M * holgura_c

    # 7. Capacidad de personal de soporte por bloque
    for r in roles_soporte:
        for t in bloques_tiempo:
            modelo += xsum(requerimiento_soporte[(i, r)] * var_cirugia_activa_en_bloque[(i, t)] for i in ids_cirugias) <= capacidad_soporte[r]

    # OPTIMIZACIÓN
    status = modelo.optimize()

    # RESULTADOS
    resultados = {
        "status": status.name,
        "objetivo": modelo.objective_value if status in [OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE] else 0,
        "programadas": [],
        "gap": modelo.gap if status in [OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE] else None,
    }

    if status in (OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE):
        for i in ids_cirugias:
            for q in ids_quirofanos:
                for t in bloques_tiempo:
                    if (i, q, t) in var_asignacion_inicio and var_asignacion_inicio[(i, q, t)].x > 0.5:
                        cir_asig = next((c for c in cirujanos_validos_por_cirugia[i] if var_asignacion_cirujano[(i, c)].x > 0.5), None)
                        resultados["programadas"].append({
                            "id": i,
                            "nombre": nombre_cirugia[i],
                            "quirofano": q,
                            "inicio": t,
                            "fin_operacion": t + bloques_operacion[i] - 1,
                            "fin_limpieza": t + duracion_total[i] - 1,
                            "cirujano_id": cir_asig,
                            "cirujano_nombre": nombre_cirujano.get(cir_asig, "—"),
                            "prioridad": prioridad_cirugia[i],
                            "contaminada": es_contaminada[i],
                            "especialidad": especialidad_requerida[i]
                        })
        resultados["programadas"].sort(key=lambda x: (x["quirofano"], x["inicio"]))

    return resultados

if __name__ == "__main__":
    cirugias, cirujanos, soporte = obtener_datos_por_defecto()
    res = optimizar_asignacion_quirofanos(cirugias, cirujanos, soporte)
    print(f"Status: {res['status']}, Objetivo: {res['objetivo']}")
    for p in res['programadas']:
        print(f"Q{p['quirofano']} | {p['inicio']:>2} -> {p['fin_limpieza']:>2} | {p['nombre']} (Contaminada: {bool(p['contaminada'])})")