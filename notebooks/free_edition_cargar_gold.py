# Databricks notebook source
# Prueba de carga de gold en Databricks Free Edition.
#
# ORIGEN = "repo":    lee los parquet de la carpeta gold/ del Git folder (repo clonado en Databricks).
# ORIGEN = "volumen": lee los parquet de un volumen "gold" al que se subieron a mano
#                     (Catalog > tu catálogo > default > crear volumen "gold" > Upload to this volume).
ORIGEN = "repo"

import os
import pandas as pd
from pyspark.sql import functions as F

cat = spark.sql("select current_catalog()").first()[0]

if ORIGEN == "repo":
    carpeta = f"{os.path.dirname(os.getcwd())}/gold"     # el notebook está en TFM/notebooks
    print("carpeta gold:", carpeta, os.listdir(carpeta))
    ses = spark.createDataFrame(pd.read_parquet(f"{carpeta}/gold_sesiones.parquet"))
    rol = spark.createDataFrame(pd.read_parquet(f"{carpeta}/gold_carga_rolling.parquet"))
else:
    spark.sql(f"create volume if not exists {cat}.default.gold")
    carpeta = f"/Volumes/{cat}/default/gold"
    print("carpeta gold:", carpeta)
    display(dbutils.fs.ls(carpeta))
    ses = spark.read.parquet(f"{carpeta}/gold_sesiones.parquet")
    rol = spark.read.parquet(f"{carpeta}/gold_carga_rolling.parquet")

# COMMAND ----------
# Comparar con lo que mostró scripts/verificar_gold.py en el computador
print("gold_sesiones:", ses.count(), "esperado 9792")
print("gold_carga_rolling:", rol.count(), "esperado 23671")
ses.printSchema()

# COMMAND ----------
# Controles de coherencia
ses.groupBy("equipo", F.year("fecha").alias("anio")).agg(
    F.count("*").alias("sesiones"),
    F.countDistinct("jugadora").alias("jugadoras"),
    F.round(F.avg("duracion_min"), 0).alias("dur_prom"),
    F.round(F.avg("dist_m"), 0).alias("dist_prom")).orderBy("equipo", "anio").show()
# esperado: TeamA 2020 2283 | TeamA 2021 2892 | TeamB 2020 1801 | TeamB 2021 2816

con = ses.filter("carga_subj is not null")
print("n con dato subjetivo:", con.count(), "(esperado 7788)")
print("corr dist_m vs carga_subj:", round(con.stat.corr("dist_m", "carga_subj"), 2), "(esperado 0.34)")

# COMMAND ----------
# Guardar como tablas para trabajar con SQL
ses.write.mode("overwrite").saveAsTable(f"{cat}.default.gold_sesiones")
rol.write.mode("overwrite").saveAsTable(f"{cat}.default.gold_carga_rolling")
display(spark.sql(f"select count(*) as filas from {cat}.default.gold_sesiones"))
