-- Gold: carga externa aguda y crónica por jugadora, con calendario completo.
-- Los días sin sesión cuentan como carga 0 (descanso). Medidas sobre distancia total y alta velocidad:
--   aguda   = suma de los últimos 7 días
--   crónica = promedio semanal de los últimos 28 días (suma 28 días / 4)
--   acwr    = aguda / crónica (solo con 28 días de historia de la jugadora)
--   monotonía = media diaria / desviación de los últimos 7 días; tensión = aguda * monotonía
with rango as (
    select jugadora, min(fecha) as f0, max(fecha) as f1
    from {{ ref('gold_sesiones') }}
    group by jugadora
),
calendario as (
    select r.jugadora, cast(d.d as date) as fecha, r.f0
    from rango r,
         lateral (select unnest(generate_series(r.f0, r.f1, interval 1 day)) as d) d
),
diario as (
    select
        c.jugadora,
        c.fecha,
        c.f0,
        coalesce(g.dist_m, 0)     as dist_m,
        coalesce(g.dist_hsr_m, 0) as dist_hsr_m,
        g.jugadora is not null    as hubo_sesion
    from calendario c
    left join {{ ref('gold_sesiones') }} g using (jugadora, fecha)
),
ventanas as (
    select
        *,
        sum(dist_m)     over w7  as dist_aguda_m,
        sum(dist_m)     over w28 / 4.0 as dist_cronica_m,
        sum(dist_hsr_m) over w7  as hsr_agudo_m,
        sum(dist_hsr_m) over w28 / 4.0 as hsr_cronico_m,
        avg(dist_m)     over w7  as media7,
        stddev_pop(dist_m) over w7 as desv7
    from diario
    window
        w7  as (partition by jugadora order by fecha rows between 6  preceding and current row),
        w28 as (partition by jugadora order by fecha rows between 27 preceding and current row)
)
select
    jugadora, fecha, hubo_sesion, dist_m, dist_hsr_m,
    dist_aguda_m, dist_cronica_m,
    case when date_diff('day', f0, fecha) >= 27 and dist_cronica_m > 0
         then dist_aguda_m / dist_cronica_m end as acwr_dist,
    hsr_agudo_m, hsr_cronico_m,
    case when date_diff('day', f0, fecha) >= 27 and hsr_cronico_m > 0
         then hsr_agudo_m / hsr_cronico_m end as acwr_hsr,
    case when desv7 > 0 then media7 / desv7 end as monotonia_dist,
    case when desv7 > 0 then dist_aguda_m * (media7 / desv7) end as tension_dist
from ventanas
