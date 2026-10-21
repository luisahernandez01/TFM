# Databricks notebook source
# Prueba de carga de gold en Databricks Free Edition.
# Antes: subir gold_sesiones.parquet y gold_carga_rolling.parquet (carpeta gold/ del repo)
# al volumen "gold" (Catalog > tu catálogo > default > gold > Upload to this volume).
from pyspark.sql import functions as F

cat = spark.sql("select current_catalog()").first()[0]
esq = "default"
spark.sql(f"create volume if not exists {cat}.{esq}.gold")
ruta = f"/Volumes/{cat}/{esq}/gold"
print("ruta:", ruta)
display(dbutils.fs.ls(ruta))

# COMMAND ----------
# Leer los parquet y comparar con lo que mostró scripts/verificar_gold.py en el computador
ses = spark.read.parquet(f"{ruta}/gold_sesiones.parquet")
rol = spark.read.parquet(f"{ruta}/gold_carga_rolling.parquet")

ESPERADO = {"gold_sesiones": 9792, "gold_carga_rolling": 23671}
print("gold_sesiones:", ses.count(), "esperado", ESPERADO["gold_sesiones"])
print("gold_carga_rolling:", rol.count(), "esperado", ESPERADO["gold_carga_rolling"])
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
ses.write.mode("overwrite").saveAsTable(f"{cat}.{esq}.gold_sesiones")
rol.write.mode("overwrite").saveAsTable(f"{cat}.{esq}.gold_carga_rolling")
display(spark.sql(f"select count(*) as filas from {cat}.{esq}.gold_sesiones"))
