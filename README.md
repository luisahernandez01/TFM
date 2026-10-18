# TFM: Visual Analytics para el monitoreo de carga en deporte (SoccerMon)

Trabajo Fin de Máster, UNIR, Máster en Análisis y Visualización de Datos Masivos.
Dataset: SoccerMon (Zenodo, DOI 10.5281/zenodo.10033832).

## Arquitectura de datos (medallón)

| Capa | Dónde | Contenido |
|------|-------|-----------|
| bronze | Azure Blob / ADLS Gen2, contenedor `bronce`, volumen `bronce_vol` | Zips originales y parquet extraídos |
| silver | Delta en Azure Databricks | Una fila por jugadora y día, con banderas de calidad; subjetivo en formato largo |
| gold | dbt Core sobre SQL warehouse | Indicadores de carga. Se exportan en parquet/CSV para Databricks Free Edition y Power BI |

## Estructura

- `infra/`: comandos y notas de la infraestructura en Azure.
- `src/extraccion/`: extracción de zips a parquet (Python, porque Spark no lee dentro de un zip).
- `src/silver/`: construcción de silver (celdas de Databricks en formato .py).
- `notebooks/`: exploración de datos para decidir los indicadores de gold.
- `dbt/`: modelos silver y gold en SQL.
- `patrones/`: detección de patrones (Andrés).
- `powerbi/`: visualización y evaluación (Paula).
- `docs/`: diagramas y notas para la memoria.

## Reparto

Lu: integración y procesamiento masivo (bronze, silver, gold). Andrés: indicadores y patrones. Paula: visualización y evaluación.
