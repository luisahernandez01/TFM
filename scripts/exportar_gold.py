"""Exporta las tablas gold a parquet y CSV en data/gold/ para Power BI y Databricks Free Edition.
Uso: python scripts/exportar_gold.py [ruta_a_tfm.duckdb] [carpeta_salida]"""
import sys, os, duckdb
db = sys.argv[1] if len(sys.argv) > 1 else "data/tfm.duckdb"
out = sys.argv[2] if len(sys.argv) > 2 else "data/gold"
os.makedirs(out, exist_ok=True)
c = duckdb.connect(db, read_only=True)
for t in ["gold_sesiones", "gold_carga_rolling"]:
    c.sql(f"copy {t} to '{out}/{t}.parquet' (format parquet)")
    c.sql(f"copy {t} to '{out}/{t}.csv' (header, delimiter ',')")
    print(t, "->", out)
