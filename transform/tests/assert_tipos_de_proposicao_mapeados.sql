-- ADR-007: um tipo de proposição que não está no seed vira "outra". Avisa, sem interromper o deploy.
{{ config(severity='warn') }}

select distinct p.sigla_tipo
from {{ ref('stg_camara_api__proposicoes') }} as p
left join {{ ref('mapa_tipos_proposicao') }} as m
    on p.sigla_tipo = m.sigla_tipo
where m.sigla_tipo is null
