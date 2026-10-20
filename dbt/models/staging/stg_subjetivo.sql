-- Silver subjetivo en formato largo (jugadora, fecha, medida, valor), una fila por medida y día.
select * exclude (rn)
from (
    select
        jugadora,
        cast(fecha as date) as fecha,
        medida,
        valor,
        row_number() over (partition by jugadora, cast(fecha as date), medida order by valor) as rn
    from read_parquet('{{ var("data_dir") }}/silver_subjetivo.parquet')
)
where rn = 1
