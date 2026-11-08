-- Contrato canônico (ADR-003, ADR-007): uma linha por proposição e parlamentar da bancada.
with autorias as (
    {% for fonte in var('fontes_ativas') %}
    select * from {{ ref('int_' ~ fonte ~ '__proposicao') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)

select
    a.proposicao_sk,
    a.parlamentar_sk,
    a.mes_ref,
    a.tipo_sigla,
    a.tipo_categoria,
    a.numero,
    a.ano,
    a.ementa,
    a.papel_autoria,
    a.data_apresentacao,
    a.fonte,
    a._carregado_em,
    '1.1.0' as _versao_contrato
from autorias as a
inner join {{ ref('dim_parlamentar') }} as d
    on a.parlamentar_sk = d.parlamentar_sk
