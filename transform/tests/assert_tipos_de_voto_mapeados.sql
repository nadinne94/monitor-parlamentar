-- ADR-008: um valor de voto desconhecido precisa ser analisado antes de chegar ao site.
-- Diferente do teste dos tipos de proposição, este interrompe o build.
select distinct v.tipo_voto
from {{ ref('stg_camara_api__votos') }} as v
left join {{ ref('mapa_tipos_voto') }} as m
    on v.tipo_voto = m.tipo_voto
where m.tipo_voto is null
