-- A legislatura 58 começa em fevereiro de 2027. Devolve as linhas que contrariam isso.
select mes_ref, legislatura
from {{ ref('dim_mes') }}
where (mes_ref = date '2027-01-01' and legislatura <> 57)
   or (mes_ref = date '2027-02-01' and legislatura <> 58)
