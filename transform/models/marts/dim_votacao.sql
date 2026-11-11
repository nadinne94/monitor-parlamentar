-- Contrato canônico (ADR-003, ADR-008): uma linha por votação nominal.
with votacoes as (
    {% for fonte in var('fontes_ativas') %}
    select * from {{ ref('int_' ~ fonte ~ '__votacao') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)

select
    votacao_sk,
    id_fonte,
    data_votacao,
    mes_ref,
    descricao,
    aprovacao,
    votos_sim,
    votos_nao,
    votos_abstencao,
    total_votos,
    fonte,
    _carregado_em,
    '1.2.0' as _versao_contrato
from votacoes
