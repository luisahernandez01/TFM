-- Silver objetivo exportado desde Databricks. Se garantiza una fila por jugadora y día:
-- algunos meses se escribieron dos veces en el procesamiento, por eso se deduplica aquí.
select * exclude (rn)
from (
    select
        *,
        row_number() over (partition by jugadora, fecha order by filas desc) as rn
    from read_parquet('{{ var("data_dir") }}/silver_objetivo.parquet')
)
where rn = 1
