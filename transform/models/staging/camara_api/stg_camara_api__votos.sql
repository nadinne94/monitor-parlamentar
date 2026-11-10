-- Staging: uma linha por votação e deputado que registrou voto, de todas as UFs.
select
    id_votacao,
    id_deputado,
    sigla_uf,
    tipo_voto,
    data_registro_voto,
    _carregado_em
from {{ source('camara_api', 'votos') }}
