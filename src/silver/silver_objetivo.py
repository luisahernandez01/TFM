# Databricks notebook source
# Silver objetivo: una fila por jugadora y día, a partir de los parquet de bronze.
from pyspark.sql import functions as F

base = "/Volumes/soccermonetl/tfm/bronce_vol"
MES = "2020-06"   # un mes por ejecución; si repites un mes, bórralo antes (modo append)

df = (spark.read.parquet(f"{base}/extraido/{MES[:4]}/{MES}/*/*.parquet")
      .withColumn("ruta", F.col("_metadata.file_path"))
      .withColumn("fecha", F.to_date(F.regexp_extract("ruta", r"/(\d{4}-\d{2}-\d{2})-Team", 1)))
      .withColumn("equipo", F.regexp_extract("ruta", r"-(Team[AB])-", 1))
      .withColumn("uuid", F.regexp_extract("ruta", r"Team[AB]-([0-9a-f\-]{36})\.parquet", 1))
      .drop("ruta")
      .withColumn("gps_invalido", ((F.col("lat") == 0) & (F.col("lon") == 0)).cast("int"))
      .withColumn("hr_valido", (F.col("heart_rate") > 0).cast("int"))
      .withColumn("acc_mag", F.sqrt(F.col("accl_x")**2 + F.col("accl_y")**2 + F.col("accl_z")**2)))

def banda(lo, hi=None):
    c = (F.col("speed") >= lo) if hi is None else ((F.col("speed") >= lo) & (F.col("speed") < hi))
    return F.avg(c.cast("int"))

silver = (df.groupBy("equipo", "uuid", "fecha").agg(
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
    banda(5.5).alias("fr_hsr"),          # alta velocidad: >= 5.5 m/s (19.8 km/h), incluye sprint
    banda(6.94).alias("fr_sprint"),      # sprint: >= 6.94 m/s (25 km/h)
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

silver.write.format("delta").mode("append").save(f"{base}/silver/objetivo")
