-- Cada parlamentar tem no máximo um voto em cada votação. Devolve as duplicatas.
select votacao_sk, parlamentar_sk, count(*) as ocorrencias
from {{ ref('fato_voto') }}
group by votacao_sk, parlamentar_sk
having count(*) > 1
