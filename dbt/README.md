# dbt (DuckDB local)

Silver y gold se construyen con dbt Core sobre DuckDB, sin necesidad de ninguna cuenta en la nube.

1. Pon `silver_objetivo.parquet` y `silver_subjetivo.parquet` (exportados desde Databricks) en la carpeta `data/` de la raíz del repo.
2. `pip install dbt-duckdb`
3. Desde esta carpeta: `dbt build --profiles-dir .`

El resultado queda en `data/tfm.duckdb` (tablas `gold_sesiones` y `gold_carga_rolling`).
Para probar sin datos reales: `python scripts/datos_sinteticos.py data_test` y luego `dbt build --profiles-dir . --vars '{data_dir: ../data_test}'`.
