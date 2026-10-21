# Databricks notebook source
# Prueba de carga de gold en Databricks Free Edition.
# Con el repo clonado como Git folder, los parquet de la carpeta gold/ ya están en el espacio de trabajo.
import os
import pandas as pd
from pyspark.sql import functions as F

raiz = os.path.dirname(os.getcwd())          # el notebook está en TFM/notebooks, la raíz es TFM
carpeta = f"{raiz}/gold"
print("carpeta gold:", carpeta)
print(os.listdir(carpeta))

# COMMAND ----------
# Leer los parquet y comparar con lo que mostró scripts/verificar_gold.py en el computador
ses = spark.createDataFrame(pd.read_parquet(f"{carpeta}/gold_sesiones.parquet"))
rol = spark.createDataFrame(pd.read_parquet(f"{carpeta}/gold_carga_rolling.parquet"))

print("gold_sesiones:", ses.count(), "esperado 9792")
print("gold_carga_rolling:", rol.count(), "esperado 23671")
ses.printSchema()

# COMMAND ----------
# Controles de coherencia: deben coincidir con la verificación local
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
cat = spark.sql("select current_catalog()").first()[0]
ses.write.mode("overwrite").saveAsTable(f"{cat}.default.gold_sesiones")
rol.write.mode("overwrite").saveAsTable(f"{cat}.default.gold_carga_rolling")
display(spark.sql(f"select count(*) as filas from {cat}.default.gold_sesiones"))

# COMMAND ----------
# Alternativa si el notebook no puede leer la carpeta del repo: subir los parquet a un volumen
# (Catalog > tu catálogo > default > crear volumen "gold" > Upload) y leer con:
# ses = spark.read.parquet(f"/Volumes/{cat}/default/gold/gold_sesiones.parquet")
