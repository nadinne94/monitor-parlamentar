-- Staging: uma linha por proposição e autor, juntando todos os meses coletados.
select
    id_proposicao,
    id_deputado,
    nome,
    tipo,
    cod_tipo,
    ordem_assinatura,
    proponente,
    _carregado_em
from {{ source('camara_api', 'autores') }}
