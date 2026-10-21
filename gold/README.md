# Tablas gold

Dos tablas, cada una en parquet (recomendado, conserva los tipos) y CSV. Generadas con dbt (`dbt/`) a partir de silver.

| Tabla | Filas | Qué es |
|---|---|---|
| `gold_sesiones` | 9,792 | Una fila por sesión válida (jugadora y día): indicadores de carga externa y medidas subjetivas del mismo día |
| `gold_carga_rolling` | 23,671 | Una fila por jugadora y día de calendario (incluye descansos): carga aguda, crónica, ACWR, monotonía y tensión |

Equipos y temporadas: TeamA y TeamB, 2020 (junio a diciembre) y 2021 (febrero a noviembre). Llave para unir tablas: `jugadora` + `fecha`.

## Sesión válida

Una sesión entra en `gold_sesiones` si cumple todo esto (umbrales en `dbt/dbt_project.yml`):
- duración entre 20 y 240 minutos
- menos de 20 % de lecturas de GPS inválidas
- velocidad máxima de 12 m/s o menos
- distancia media entre 5 y 150 m/min

## gold_sesiones

| Columna | Descripción |
|---|---|
| `jugadora`, `equipo`, `fecha` | Identificador anónimo (`TeamX-uuid`), equipo y día |
| `duracion_min` | Duración de la sesión en minutos |
| `dist_m` | Distancia total en metros, calculada a partir de la velocidad que registra el dispositivo |
| `dist_por_min` | `dist_m` / `duracion_min` |
| `dist_hsr_m` | Distancia a alta velocidad (5.5 m/s o más, 19.8 km/h) |
| `dist_sprint_m` | Distancia en sprint (6.94 m/s o más, 25 km/h). Está incluida en `dist_hsr_m` |
| `speed_max`, `speed_p95` | Velocidad máxima y percentil 95 (m/s) |
| `impulso_por_min` | Suma del impulso de aceleración / minutos |
| `acc_mag_media` | Magnitud media de la aceleración (casi constante, aporta poco) |
| `cobertura_hr`, `ok_hr` | Proporción de lecturas de pulso válidas y si supera 50 % |
| `carga_subj` | Carga diaria subjetiva (`daily_load`) |
| `acwr_subj`, `monotony_subj`, `strain_subj` | Indicadores subjetivos ya calculados en el dataset |
| `readiness`, `fatiga`, `dolor_muscular`, `calidad_sueno`, `horas_sueno`, `estres`, `animo` | Bienestar reportado por la jugadora |
| `tiene_subjetivo` | Si hay algún dato subjetivo ese día |

## gold_carga_rolling

Los días sin sesión cuentan como carga 0.

| Columna | Descripción |
|---|---|
| `dist_m`, `dist_hsr_m` | Carga del día |
| `hubo_sesion` | Si hubo sesión válida ese día |
| `dist_aguda_m`, `hsr_agudo_m` | Suma de los últimos 7 días |
| `dist_cronica_m`, `hsr_cronico_m` | Promedio semanal de los últimos 28 días (suma / 4) |
| `acwr_dist`, `acwr_hsr` | Aguda / crónica. Solo con 28 días de historia de la jugadora |
| `monotonia_dist` | Media diaria / desviación de los últimos 7 días |
| `tension_dist` | Carga aguda * monotonía |

## Advertencias

- **Valores extremos que quedan.** Tras los filtros aún hay pocas sesiones con valores altos (por ejemplo `dist_m` hasta 27.6 km, con percentil 99 de 14 km). Para comparar conviene usar medianas, percentiles y correlación de Spearman en lugar de promedios simples.
- **Pulso cardíaco.** La cobertura es muy desigual: casi nula en TeamB 2020 (agosto a octubre) y de 40 a 80 % en TeamA y en 2021. No se puede usar de forma pareja entre equipos y temporadas.
- **Datos subjetivos incompletos.** 8 de las 17 jugadoras de TeamB con GPS en junio de 2020 no aparecen en ningún archivo subjetivo, y las medidas de bienestar las reporta menos de la mitad de los días. 7,788 de las 9,792 sesiones tienen algún dato subjetivo.
- **Unidades.** La velocidad se asume en m/s (máximos de 8 a 9 m/s en sesiones normales, coherente con fútbol), pero no se ha verificado en la documentación del dataset. La distancia se calcula a partir de la velocidad del dispositivo, no de las posiciones GPS.
- **Orden de magnitud de la relación con la carga subjetiva.** Correlación de Spearman con `carga_subj`: distancia total 0.35, distancia por minuto 0.29, impulso por minuto 0.26, duración 0.25, alta velocidad 0.22, sprint 0.18, velocidad máxima 0.17. Es una relación moderada.
- **Datos de origen.** SoccerMon (Zenodo, DOI 10.5281/zenodo.10033832). Citar la fuente y confirmar la licencia en Zenodo antes de difundir.
