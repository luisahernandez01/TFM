{% test dbt_utils_free_unique_combo(model) %}
-- falla si hay más de una fila por jugadora y fecha
select jugadora, fecha, count(*) as n
from {{ model }}
group by jugadora, fecha
having count(*) > 1
{% endtest %}
