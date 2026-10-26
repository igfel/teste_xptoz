select
    dominio_email,
    count(*) as total_registros,
    now() as created_at,
    now() as updated_at
from {{ ref('int_users_info') }}
group by dominio_email
