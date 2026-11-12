-- Staging: uma linha por votação do Plenário, juntando todos os meses coletados.
select
    id,
    data_hora_registro,
    sigla_orgao,
    descricao,
    aprovacao,
    proposicao_objeto,
    uri_evento,
    nominal,
    _carregado_em
from {{ source('camara_api', 'votacoes') }}
