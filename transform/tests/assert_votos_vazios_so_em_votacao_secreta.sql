-- ADR-008: votos sem tipo só são aceitos quando a votação inteira vem assim (votação secreta).
-- Uma votação com alguns votos vazios e outros preenchidos é um caso desconhecido: para o build.
select
    id_votacao,
    count(*) as votos,
    count(tipo_voto) as votos_com_tipo
from {{ ref('stg_camara_api__votos') }}
group by id_votacao
having count(tipo_voto) > 0 and count(tipo_voto) < count(*)
