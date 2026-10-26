select
    id,
    upper(regexp_replace(trim(nome), '[[:space:]]+', ' ', 'g')) as nome,
    upper(trim(email)) as email,
    idade,
    upper(trim(cidade)) as cidade,
    now() as created_at,
    now() as updated_at
from {{ source('raw', 'users_info') }}
