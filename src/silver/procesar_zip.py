# Databricks notebook source
# Procesa un zip objetivo completo, mes a mes: extrae, agrega a silver y limpia lo extraído.
# Se salta los meses que ya están en silver. Cambia solo ZIP.
import zipfile, os, shutil, time, re
from pyspark.sql import functions as F

base = "/Volumes/soccermonetl/tfm/bronce_vol"
ZIP = "objective-TeamB-2020.zip"
SILVER = f"{base}/silver/objetivo"
equipo_zip = re.search(r"(Team[AB])", ZIP).group(1)

def banda(lo, hi=None):
    c = (F.col("speed") >= lo) if hi is None else ((F.col("speed") >= lo) & (F.col("speed") < hi))
    return F.avg(c.cast("int"))

TIPOS = {"lat": "double", "lon": "double", "speed": "double", "inst_acc_impulse": "double",
         "accl_x": "double", "accl_y": "double", "accl_z": "double",
         "gyro_x": "double", "gyro_y": "double", "gyro_z": "double",
         "heart_rate": "long", "hacc": "long", "hdop": "long",
         "signal_quality": "long", "num_satellites": "long"}

def leer_parquets(patron):
    """Lee los parquet de un mes agrupados por esquema real y los lleva a tipos fijos.
    Evita el error de tipo cuando un archivo trae INT64 donde otros traen double."""
    import glob
    import pyarrow.parquet as pq
    grupos = {}
    for a in sorted(glob.glob(patron)):
        firma = tuple((c.name, str(c.type)) for c in pq.read_schema(a))
        grupos.setdefault(firma, []).append(a)
    if len(grupos) > 1:
        print("   esquemas distintos en el mes:", len(grupos))
    partes = []
    for firma, lista in grupos.items():
        d = spark.read.parquet(*lista)
        partes.append(d.select("player_name", "time",
                               *[F.col(c).cast(t).alias(c) for c, t in TIPOS.items()],
                               F.col("_metadata.file_path").alias("ruta")))
    out = partes[0]
    for q in partes[1:]:
        out = out.unionByName(q)
    return out

def silver_mes(patron):
    df = (leer_parquets(patron)
          .withColumn("fecha", F.to_date(F.regexp_extract("ruta", r"/(\d{4}-\d{2}-\d{2})-Team", 1)))
          .withColumn("equipo", F.regexp_extract("ruta", r"-(Team[AB])-", 1))
          .withColumn("uuid", F.regexp_extract("ruta", r"Team[AB]-([0-9a-f\-]{36})\.parquet", 1))
          .drop("ruta")
          .withColumn("gps_invalido", ((F.col("lat") == 0) & (F.col("lon") == 0)).cast("int"))
          .withColumn("hr_valido", (F.col("heart_rate") > 0).cast("int"))
          .withColumn("acc_mag", F.sqrt(F.col("accl_x")**2 + F.col("accl_y")**2 + F.col("accl_z")**2)))
    return (df.groupBy("equipo", "uuid", "fecha").agg(
        F.count("*").alias("filas"),
        F.countDistinct("time").alias("tiempos_unicos"),
        F.avg("gps_invalido").alias("pct_gps_invalido"),
        F.avg((F.col("hdop") > 5).cast("int")).alias("pct_hdop_mayor_5"),
        F.avg("hr_valido").alias("cobertura_hr"),
        F.avg(F.when(F.col("hr_valido") == 1, F.col("heart_rate"))).alias("hr_media"),
        F.max(F.when(F.col("hr_valido") == 1, F.col("heart_rate"))).alias("hr_max"),
        F.max("speed").alias("speed_max"),
        F.avg("speed").alias("speed_media"),
        F.percentile_approx("speed", 0.95).alias("speed_p95"),
        banda(0, 0.5).alias("fr_parado"), banda(0.5, 2).alias("fr_caminar"),
        banda(2, 4).alias("fr_trote"), banda(4, 5.5).alias("fr_carrera"),
        banda(5.5).alias("fr_hsr"), banda(6.94).alias("fr_sprint"),
        F.avg("acc_mag").alias("acc_mag_media"),
        F.percentile_approx("acc_mag", 0.99).alias("acc_mag_p99"),
        F.sum("inst_acc_impulse").alias("impulso_acc_suma"))
      .withColumn("jugadora", F.concat_ws("-", "equipo", "uuid"))
      .withColumn("duracion_min", F.col("tiempos_unicos") * 0.1 / 60)
      .withColumn("dist_m", F.col("speed_media") * F.col("tiempos_unicos") * 0.1)
      .withColumn("dist_hsr_m", F.col("fr_hsr") * F.col("dist_m"))
      .withColumn("dist_sprint_m", F.col("fr_sprint") * F.col("dist_m"))
      .withColumn("ok_duracion", F.col("duracion_min") >= 20)
      .withColumn("ok_gps", F.col("pct_gps_invalido") < 0.2)
      .withColumn("ok_hr", F.col("cobertura_hr") >= 0.5))

# meses ya procesados de este equipo
try:
    hechos = {r.mes for r in (spark.read.format("delta").load(SILVER)
              .filter(F.col("equipo") == equipo_zip)
              .select(F.date_format("fecha", "yyyy-MM").alias("mes")).distinct().collect())}
except Exception:
    hechos = set()

with zipfile.ZipFile(f"{base}/{ZIP}") as z:
    por_mes = {}
    for m in z.infolist():
        g = re.match(r"(\d{4})/(\d{4}-\d{2})/", m.filename)
        if g and not m.is_dir():
            por_mes.setdefault(g.group(2), []).append(m)
    print("meses en el zip:", sorted(por_mes), "| ya hechos:", sorted(hechos))

    t_total = time.time()
    for mes in sorted(por_mes):
        if mes in hechos:
            continue
        t0 = time.time()
        for m in por_mes[mes]:
            destino = f"{base}/extraido/{m.filename}"
            if os.path.exists(destino) and os.path.getsize(destino) == m.file_size:
                continue
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with z.open(m) as src, open(destino, "wb") as dst:
                shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
        t1 = time.time()
        silver_mes(f"{base}/extraido/{mes[:4]}/{mes}/*/*.parquet") \
            .write.format("delta").mode("append").save(SILVER)
        shutil.rmtree(f"{base}/extraido/{mes[:4]}/{mes}", ignore_errors=True)
        print(mes, len(por_mes[mes]), "archivos | extracción", round((t1 - t0) / 60, 1),
              "min | silver", round((time.time() - t1) / 60, 1), "min")
print("total", round((time.time() - t_total) / 60, 1), "min")
