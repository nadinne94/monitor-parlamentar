-- Adaptador: quantas votações o Plenário fez em cada mês, e quantas foram nominais (ADR-008, seção 5).
select
    cast(date_trunc('month', data_hora_registro) as date) as mes_ref,
    count(*) as votacoes_plenario,
    count(*) filter (where nominal) as votacoes_nominais,
    'camara_api' as fonte
from {{ ref('stg_camara_api__votacoes') }}
group by all
