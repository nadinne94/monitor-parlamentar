-- Contrato canônico (ADR-003, ADR-008): uma linha por votação nominal e parlamentar da bancada.
-- Quem estava na bancada e não aparece entre os votos registrados recebe 'sem_registro'.
with votos as (
    {% for fonte in var('fontes_ativas') %}
    select * from {{ ref('int_' ~ fonte ~ '__voto') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)

select
    v.votacao_sk,
    p.parlamentar_sk,
    v.mes_ref,
    coalesce(vt.voto, 'sem_registro') as voto,
    v.fonte,
    v._carregado_em,
    '1.2.0' as _versao_contrato
from {{ ref('dim_votacao') }} as v
cross join {{ ref('dim_parlamentar') }} as p
left join votos as vt
    on vt.votacao_sk = v.votacao_sk
    and vt.parlamentar_sk = p.parlamentar_sk
where p.em_exercicio
