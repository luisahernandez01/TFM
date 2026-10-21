"""Revisa que las tablas de dbt tengan sentido. Uso: python scripts/verificar_gold.py [ruta_a_tfm.duckdb]"""
import sys, duckdb
db = sys.argv[1] if len(sys.argv) > 1 else "data/tfm.duckdb"
c = duckdb.connect(db, read_only=True)
q = lambda sql: c.sql(sql).fetchall()

print("== Filas ==")
for t in ["stg_objetivo", "stg_subjetivo", "gold_sesiones", "gold_carga_rolling"]:
    print(f"{t:22s}", q(f"select count(*) from {t}")[0][0])

print("\n== stg_objetivo: filas totales vs jugadora-día únicos (deben ser iguales) ==")
print(q("select count(*), count(distinct (jugadora, fecha)) from stg_objetivo")[0])

print("\n== Sesiones descartadas por regla (sobre las que ya pasan duración mínima y GPS) ==")
base = "from stg_objetivo where duracion_min >= 20 and pct_gps_invalido < 0.2"
print("speed_max > 12 m/s:", q(f"select count(*) {base} and speed_max > 12")[0][0])
print("duracion > 240 min:", q(f"select count(*) {base} and duracion_min > 240")[0][0])
print("dist_por_min > 150:", q(f"select count(*) {base} and dist_m / duracion_min > 150")[0][0])
print("dist_por_min < 5:  ", q(f"select count(*) {base} and dist_m / duracion_min < 5")[0][0])

print("\n== Sesiones válidas por equipo y año ==")
for r in q("select equipo, year(fecha) anio, count(*) n, count(distinct jugadora) jug, "
           "round(avg(duracion_min),0) dur_prom, round(avg(dist_m),0) dist_prom, "
           "round(avg(tiene_subjetivo::int),2) con_subj from gold_sesiones group by 1,2 order by 1,2"):
    print(r)

print("\n== Rangos de los indicadores (min, mediana, p99, max) ==")
for col in ["duracion_min", "dist_m", "dist_por_min", "dist_hsr_m", "dist_sprint_m", "speed_max", "impulso_por_min"]:
    print(col, q(f"select round(min({col}),1), round(median({col}),1), "
                 f"round(quantile_cont({col},0.99),1), round(max({col}),1) from gold_sesiones")[0])

print("\n== Correlación con la carga subjetiva (solo días con dato subjetivo) ==")
for col in ["duracion_min", "dist_m", "dist_por_min", "dist_hsr_m", "dist_sprint_m", "speed_max", "impulso_por_min"]:
    r = q(f"select round(corr({col}, carga_subj),3), count(*) from gold_sesiones where carga_subj is not null")[0]
    print(f"{col:16s} r={r[0]}  n={r[1]}")

print("\n== Correlación de Spearman (por rangos, robusta a valores extremos) ==")
for col in ["duracion_min", "dist_m", "dist_por_min", "dist_hsr_m", "dist_sprint_m", "speed_max", "impulso_por_min"]:
    r = q(f"select round(corr(a, b),3) from (select rank() over (order by {col}) a, rank() over (order by carga_subj) b "
          f"from gold_sesiones where carga_subj is not null)")[0][0]
    print(f"{col:16s} rho={r}")

print("\n== Carga rolling: ACWR de distancia (días con 28 días de historia) ==")
print(q("select count(*), count(acwr_dist), round(min(acwr_dist),2), round(median(acwr_dist),2), "
        "round(max(acwr_dist),2) from gold_carga_rolling")[0])
