-- Adaptador: votos registrados, traduzidos para o vocabulário do ADR-008.
-- Quem não registrou voto não aparece aqui: o sem_registro é inferido no mart.
select
    md5('camara_api|' || v.id_votacao) as votacao_sk,
    md5('camara_api|' || cast(v.id_deputado as varchar)) as parlamentar_sk,
    m.voto
from {{ ref('stg_camara_api__votos') }} as v
inner join {{ ref('mapa_tipos_voto') }} as m
    on v.tipo_voto = m.tipo_voto
