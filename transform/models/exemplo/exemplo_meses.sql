--vermelho
--select mes as mes_ref
--from range(date '2027-02-01', date '2028-01-01', interval 1 month) as t(mes)

--verde
-- Modelo de exemplo do esqueleto (Incremento 0).
-- Prova que dbt + DuckDB funcionam; será substituído pela dim_mes no Incremento 1.
select
    cast(mes as date) as mes_ref
from range(date '2027-02-01', date '2028-01-01', interval 1 month) as t(mes)
