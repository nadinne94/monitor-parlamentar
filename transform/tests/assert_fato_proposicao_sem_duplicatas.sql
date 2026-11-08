-- Cada parlamentar aparece no máximo uma vez em cada proposição. Devolve as duplicatas.
select proposicao_sk, parlamentar_sk, count(*) as ocorrencias
from {{ ref('fato_proposicao') }}
group by proposicao_sk, parlamentar_sk
having count(*) > 1
