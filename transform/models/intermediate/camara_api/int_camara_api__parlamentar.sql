-- Adaptador: traduz os deputados da Câmara para o formato da dim_parlamentar (ADR-003).
select
    md5('camara_api|' || cast(id as varchar)) as parlamentar_sk,
    'camara_api' as fonte,
    cast(id as varchar) as id_fonte,
    nome as nome_parlamentar,
    cast(null as varchar) as nome_civil,
    'camara_deputados' as casa,
    'federal' as esfera,
    sigla_uf as uf,
    cast(null as varchar) as municipio,
    sigla_partido as partido_atual,
    url_foto,
    true as em_exercicio,
    _carregado_em
from {{ ref('stg_camara_api__deputados') }}
