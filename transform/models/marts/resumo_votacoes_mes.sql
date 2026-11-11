-- Contrato canônico (ADR-003, ADR-008): o contexto de cada mês, para o site não mostrar
-- um número pequeno de votações nominais como se fosse pouca atividade.
with resumos as (
    {% for fonte in var('fontes_ativas') %}
    select * from {{ ref('int_' ~ fonte ~ '__resumo_votacoes') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)

select
    mes_ref,
    votacoes_plenario,
    votacoes_nominais,
    fonte,
    '1.2.0' as _versao_contrato
from resumos
