-- A dim_votacao guarda uma proposição afetada por votação: setembro e outubro de 2026 mostraram
-- exatamente uma em cada votação nominal. Se aparecer uma votação com várias, o desenho precisa
-- ser revisto antes que o site mostre só uma delas: para o build.
select id_votacao, count(*) as proposicoes
from {{ ref('stg_camara_api__afetadas') }}
group by id_votacao
having count(*) > 1
