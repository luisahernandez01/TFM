-- Gold: una fila por sesión válida (jugadora y día) con indicadores de carga externa
-- calculados con GPS e IMU, y las medidas subjetivas del mismo día cuando existen.
-- Una sesión es válida si dura lo suficiente y el GPS es confiable.
with obj as (
    select *
    from {{ ref('stg_objetivo') }}
    where duracion_min >= {{ var('min_duracion_min') }}
      and pct_gps_invalido < {{ var('max_gps_invalido') }}
),
subj as (
    select
        jugadora,
        fecha,
        max(case when medida = 'daily_load'      then valor end) as carga_subj,
        max(case when medida = 'acwr'            then valor end) as acwr_subj,
        max(case when medida = 'monotony'        then valor end) as monotony_subj,
        max(case when medida = 'strain'          then valor end) as strain_subj,
        max(case when medida = 'readiness'       then valor end) as readiness,
        max(case when medida = 'fatigue'         then valor end) as fatiga,
        max(case when medida = 'soreness'        then valor end) as dolor_muscular,
        max(case when medida = 'sleep_quality'   then valor end) as calidad_sueno,
        max(case when medida = 'sleep_duration'  then valor end) as horas_sueno,
        max(case when medida = 'stress'          then valor end) as estres,
        max(case when medida = 'mood'            then valor end) as animo
    from {{ ref('stg_subjetivo') }}
    group by jugadora, fecha
)
select
    o.jugadora,
    o.equipo,
    o.fecha,
    o.duracion_min,
    o.dist_m,
    o.dist_m / o.duracion_min          as dist_por_min,
    o.dist_hsr_m,
    o.dist_sprint_m,
    o.speed_max,
    o.speed_p95,
    o.impulso_acc_suma / o.duracion_min as impulso_por_min,
    o.acc_mag_media,
    o.cobertura_hr,
    o.ok_hr,
    s.carga_subj, s.acwr_subj, s.monotony_subj, s.strain_subj,
    s.readiness, s.fatiga, s.dolor_muscular, s.calidad_sueno, s.horas_sueno, s.estres, s.animo,
    (s.jugadora is not null) as tiene_subjetivo
from obj o
left join subj s using (jugadora, fecha)
