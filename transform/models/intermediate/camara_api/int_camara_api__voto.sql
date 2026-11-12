-- Adaptador: votos registrados, traduzidos para o vocabulário do ADR-008.
-- Quem não registrou voto não aparece aqui: o sem_registro é inferido no mart.
-- Um voto sem tipo é de votação secreta: o deputado votou, mas o voto não é divulgado.
select
    md5('camara_api|' || v.id_votacao) as votacao_sk,
    md5('camara_api|' || cast(v.id_deputado as varchar)) as parlamentar_sk,
    case when v.tipo_voto is null then 'secreto' else m.voto end as voto
from {{ ref('stg_camara_api__votos') }} as v
left join {{ ref('mapa_tipos_voto') }} as m
    on v.tipo_voto = m.tipo_voto
