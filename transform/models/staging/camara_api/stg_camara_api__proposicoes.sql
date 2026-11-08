-- Staging: uma linha por proposição, juntando todos os meses coletados.
select
    id,
    sigla_tipo,
    cod_tipo,
    numero,
    ano,
    ementa,
    data_apresentacao,
    _carregado_em
from {{ source('camara_api', 'proposicoes') }}
