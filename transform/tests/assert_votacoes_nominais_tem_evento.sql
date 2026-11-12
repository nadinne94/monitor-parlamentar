-- ADR-008: os registros sem evento são réplicas automáticas e ficam fora da frase de contexto.
-- Se uma votação nominal aparecer sem evento, essa regra deixa de valer: para o build.
select id, descricao
from {{ ref('stg_camara_api__votacoes') }}
where nominal
    and uri_evento is null
