-- Contrato canônico (ADR-003): um mês de referência por linha.
-- Cobre a legislatura 57 (fev/2023 a jan/2027) e a 58 (fev/2027 a jan/2031).
with meses as (
    select cast(mes as date) as mes_ref
    from range(date '2023-02-01', date '2031-02-01', interval 1 month) as t(mes)
)

select
    mes_ref,
    cast(year(mes_ref) as integer) as ano,
    cast(month(mes_ref) as integer) as mes,
    cast(57 + date_diff('month', date '2023-02-01', mes_ref) // 48 as integer) as legislatura,
    '1.0.0' as _versao_contrato
from meses
