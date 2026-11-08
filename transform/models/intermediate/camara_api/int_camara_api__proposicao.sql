-- Adaptador: traduz proposições e autores da Câmara para o formato do fato_proposicao (ADR-003, ADR-007).
-- Uma linha por proposição e autor deputado. A restrição à bancada acontece no mart.
select
    md5('camara_api|' || cast(p.id as varchar)) as proposicao_sk,
    md5('camara_api|' || cast(a.id_deputado as varchar)) as parlamentar_sk,
    cast(date_trunc('month', p.data_apresentacao) as date) as mes_ref,
    p.sigla_tipo as tipo_sigla,
    coalesce(m.categoria, 'outra') as tipo_categoria,
    p.numero,
    p.ano,
    p.ementa,
    case when a.ordem_assinatura = 1 then 'autor' else 'coautor' end as papel_autoria,
    cast(p.data_apresentacao as date) as data_apresentacao,
    'camara_api' as fonte,
    p._carregado_em
from {{ ref('stg_camara_api__autores') }} as a
inner join {{ ref('stg_camara_api__proposicoes') }} as p
    on a.id_proposicao = p.id
left join {{ ref('mapa_tipos_proposicao') }} as m
    on p.sigla_tipo = m.sigla_tipo
where a.id_deputado is not null
