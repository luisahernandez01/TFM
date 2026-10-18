# Databricks notebook source
# Exploración de silver para decidir los indicadores de gold.
from pyspark.sql import functions as F
base = "/Volumes/soccermonetl/tfm/bronce_vol"

s = spark.read.format("delta").load(f"{base}/silver/objetivo")
s.printSchema()
print(s.count(), s.select("jugadora").distinct().count())

# uso de cada mes
s.groupBy(F.date_format("fecha", "yyyy-MM").alias("mes")).agg(
    F.count("*").alias("dias_jug"),
    F.avg(F.col("ok_duracion").cast("int")).alias("ok_dur"),
    F.avg(F.col("ok_gps").cast("int")).alias("ok_gps"),
    F.avg(F.col("ok_hr").cast("int")).alias("ok_hr")).orderBy("mes").show(50)

# distribuciones de candidatos a indicador
s.filter("ok_duracion and ok_gps").select(
    "duracion_min", "dist_m", "speed_max", "dist_hsr_m", "dist_sprint_m", "acc_mag_media", "impulso_acc_suma"
).summary("min", "25%", "50%", "75%", "99%", "max").show()

# medidas subjetivas disponibles
sub = spark.read.format("delta").load(f"{base}/silver/subjetivo_ancho")
sub.select("medida").distinct().show(50, truncate=False)
