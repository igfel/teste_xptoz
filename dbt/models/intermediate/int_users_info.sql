with regex_data as (
    select
        *,
        trim(regexp_replace(nome, '^((SR|SRA|SRTA|DR|DRA)\.[[:space:]]+)+', ''))
            as nome_sem_titulo
    from {{ ref('stg_users_info') }}
)
select
    id,
    nome,
    nullif(split_part(nome_sem_titulo, ' ', 1), '') as primeiro_nome,
    case
        when position(' ' in nome_sem_titulo) > 0
        then reverse(split_part(reverse(nome_sem_titulo), ' ', 1))
    end as ultimo_nome,
    email,
    case
        when email ~ '^[^@[:space:]]+@[^@[:space:]]+$'
        then split_part(email, '@', 2)
    end as dominio_email,
    idade,
    cidade,
    created_at,
    updated_at
from regex_data
