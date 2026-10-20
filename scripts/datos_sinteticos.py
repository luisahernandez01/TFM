"""Genera silver_objetivo.parquet y silver_subjetivo.parquet sintéticos, con el mismo esquema
que la exportación de Databricks. Sirve solo para probar el proyecto dbt sin los datos reales."""
import numpy as np, pandas as pd, sys, os
out = sys.argv[1] if len(sys.argv) > 1 else "data_test"
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(1)
filas = []
for equipo in ["TeamA", "TeamB"]:
    for i in range(6):
        uid = f"{rng.integers(0, 16**8):08x}-0000-4000-8000-{rng.integers(0, 16**12):012x}"
        for f in pd.date_range("2020-06-01", "2020-08-31"):
            if rng.random() < 0.55:
                dur = rng.uniform(15, 140)
                sm = rng.uniform(0.2, 0.7)
                filas.append(dict(
                    equipo=equipo, uuid=uid, fecha=f.date(), filas=int(dur*6000), tiempos_unicos=int(dur*600),
                    pct_gps_invalido=rng.uniform(0, 0.05), pct_hdop_mayor_5=rng.uniform(0, 0.1),
                    cobertura_hr=rng.choice([0, 0.8]), hr_media=140.0, hr_max=190,
                    speed_max=rng.uniform(4, 9), speed_media=sm, speed_p95=sm*5,
                    fr_parado=.7, fr_caminar=.2, fr_trote=.08, fr_carrera=.02, fr_hsr=.01, fr_sprint=.003,
                    acc_mag_media=1.2, acc_mag_p99=2.5, impulso_acc_suma=dur*6000*30.0,
                    jugadora=f"{equipo}-{uid}", duracion_min=dur, dist_m=sm*dur*60,
                    dist_hsr_m=sm*dur*60*.01, dist_sprint_m=sm*dur*60*.003,
                    ok_duracion=dur >= 20, ok_gps=True, ok_hr=False))
obj = pd.DataFrame(filas)
obj = pd.concat([obj, obj.sample(30, random_state=1)])        # duplicados a propósito
obj.to_parquet(f"{out}/silver_objetivo.parquet", index=False)
medidas = ["daily_load", "acwr", "monotony", "strain", "readiness", "fatigue", "soreness",
           "sleep_quality", "sleep_duration", "stress", "mood", "weekly_load"]
sub = []
for j in obj.jugadora.unique()[:8]:
    for f in pd.date_range("2020-06-01", "2020-08-31"):
        for m in medidas:
            sub.append(dict(jugadora=j, fecha=pd.Timestamp(f), medida=m, valor=float(rng.uniform(1, 10))))
pd.DataFrame(sub).to_parquet(f"{out}/silver_subjetivo.parquet", index=False)
print("sintéticos en", out, "| filas objetivo (con duplicados):", len(obj))
