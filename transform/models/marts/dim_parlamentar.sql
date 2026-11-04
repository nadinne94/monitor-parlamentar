-- Contrato canônico (ADR-003): une os adaptadores de todas as fontes ativas.
{% for fonte in var('fontes_ativas') %}
select
    *,
    '1.0.0' as _versao_contrato
from {{ ref('int_' ~ fonte ~ '__parlamentar') }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
