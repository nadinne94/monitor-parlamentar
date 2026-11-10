-- Adaptador: votações nominais da Câmara no formato da dim_votacao (ADR-003, ADR-008).
with placar as (
    select
        id_votacao,
        count(*) filter (where tipo_voto = 'Sim') as votos_sim,
        count(*) filter (where tipo_voto = 'Não') as votos_nao,
        count(*) filter (where tipo_voto = 'Abstenção') as votos_abstencao,
        count(*) as total_votos
    from {{ ref('stg_camara_api__votos') }}
    group by id_votacao
)

select
    md5('camara_api|' || v.id) as votacao_sk,
    v.id as id_fonte,
    cast(v.data_hora_registro as date) as data_votacao,
    cast(date_trunc('month', v.data_hora_registro) as date) as mes_ref,
    v.descricao,
    v.aprovacao,
    p.votos_sim,
    p.votos_nao,
    p.votos_abstencao,
    p.total_votos,
    'camara_api' as fonte,
    v._carregado_em
from {{ ref('stg_camara_api__votacoes') }} as v
inner join placar as p
    on v.id = p.id_votacao
where v.nominal
