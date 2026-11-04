-- Staging: limpeza e tipagem, mantendo os nomes da fonte.
select
    id,
    nome,
    sigla_uf,
    id_legislatura,
    sigla_partido,
    url_foto,
    email,
    _carregado_em
from {{ source('camara_api', 'deputados') }}
