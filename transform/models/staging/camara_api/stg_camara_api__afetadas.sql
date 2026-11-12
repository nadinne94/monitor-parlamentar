-- Staging: uma linha por votação nominal e proposição afetada, juntando todos os meses coletados.
select
    id_votacao,
    id_proposicao,
    sigla_tipo,
    numero,
    ano,
    ementa,
    _carregado_em
from {{ source('camara_api', 'afetadas') }}
