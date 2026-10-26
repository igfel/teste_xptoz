# Case XPTOZ — Engenharia de Dados

O projeto gera cadastros fictícios e conta quantos registros existem por domínio
de e-mail. O Python faz a carga no PostgreSQL, o dbt organiza as transformações e
o Airflow executa o processamento uma vez por dia.

## Estrutura

```text
airflow/dags/       DAG xptoz_users
dbt/
  models/          Origem Raw e modelos Staging, Intermediate e Marts
  dbt_project.yml  Configuração dos modelos e schemas
  profiles.yml     Conexão do dbt com o banco
docker/postgres/   Criação dos bancos e usuários
scripts/           Gerador de dados e configuração inicial
docs/              Roteiro do vídeo
docker-compose.yml Serviços, portas e volumes
Dockerfile         Imagem usada pelos serviços do Airflow
requirements.txt   Dependências Python
.env.example       Variáveis de configuração
```

Em `scripts/`, o `generate_data.py` adapta o gerador fornecido no case.
O `setup_env.py` cria o `.env`; os outros dois scripts configuram o login e a
conexão do Airflow com seu banco de metadados.

## Fluxo dos dados

| Camada | Tabela | O que faz |
|---|---|---|
| Raw | `public.users_info` | Guarda os cadastros como foram gerados. |
| Staging | `analytics_staging.stg_users_info` | Padroniza os textos e acrescenta os horários de processamento. |
| Intermediate | `analytics_intermediate.int_users_info` | Extrai primeiro nome, último nome e domínio do e-mail. |
| Marts | `analytics_marts.mart_users_por_dominio` | Conta os registros por domínio. |

Essas tabelas ficam no banco `xptoz`. O banco `airflow` guarda o histórico e os
metadados da orquestração, com um usuário separado.

Os modelos usam `source()` e `ref()` para definir as dependências. A cada execução,
o dbt reconstrói as três tabelas de transformação. `created_at` e `updated_at`
registram o horário desse processamento, sem manter histórico das alterações.

## Requisitos

- Docker com containers Linux e Compose 2.20 ou superior.
- Python 3.10 ou superior para gerar o `.env`.
- Pelo menos 4 GB de memória disponíveis para os containers; 8 GB recomendados.
- Internet para baixar as imagens e dependências na primeira execução.

No Windows, o Docker Desktop precisa estar com o WSL2 funcionando. As dependências
Python são instaladas na imagem, conforme `requirements.txt`. PostgreSQL, Airflow
e dbt rodam nos containers. O DBeaver é opcional para consultar as tabelas.

## Configuração e execução

Abra o terminal na raiz do projeto, com o Docker iniciado, e execute:

```bash
python scripts/setup_env.py
docker compose up -d --build --wait
```

No Windows, também pode usar `py scripts/setup_env.py`.

O primeiro comando gera o `.env` a partir de `.env.example`. Se o arquivo já
existir, ele é mantido. As senhas dos bancos e as chaves do Airflow são geradas
automaticamente.

O segundo comando constrói a imagem e sobe o ambiente. O `airflow-init` configura
o login, aplica as migrações do Airflow e carrega os dados iniciais. Depois ficam
ativos PostgreSQL, API/interface, scheduler e DAG processor. O `airflow-init`
termina com `Exited (0)` quando conclui a preparação.

As principais configurações do `.env` são:

| Variável | Uso | Padrão |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | Nome dos recursos Docker | `xptoz_case` |
| `AIRFLOW_PORT` | Porta local da interface | `8080` |
| `POSTGRES_PORT` | Porta local do banco | `5433` |
| `AIRFLOW_ADMIN_USER` | Login no Airflow | `admin` |
| `AIRFLOW_ADMIN_PASSWORD` | Senha do login no Airflow | Gerada pelo script |
| `XPTOZ_DB_PASSWORD` | Senha do usuário `xptoz` | Gerada pelo script |
| `FAKER_SEED` | Semente do gerador | `42` |
| `DATA_ROWS` | Tentativas de inserção na carga inicial | `1000` |

A configuração completa está em `.env.example`. Para usar outras portas, ajuste
o `.env` antes de subir os serviços.

A carga usa Faker `pt_BR` e ignora e-mails repetidos com `ON CONFLICT DO NOTHING`.
Por isso, pode inserir menos de 1.000 registros. Repetir o lote com a mesma semente
não duplica os cadastros existentes. Os domínios `example.com`, `example.net` e
`example.org` vêm da versão do Faker usada no projeto.

## Airflow

Acesse **http://localhost:8080** e entre com `AIRFLOW_ADMIN_USER` e
`AIRFLOW_ADMIN_PASSWORD` do `.env`.

Abra a DAG `xptoz_users`, confira se está ativa e clique em **Trigger**.
A task `run_dbt` executa os modelos; o andamento aparece nos logs da própria task.
As tabelas analíticas ficam disponíveis após a primeira execução bem-sucedida.

Para disparar pelo terminal:

```bash
docker compose exec airflow-scheduler airflow dags trigger xptoz_users
```

A DAG é criada ativa e roda diariamente às **03h de America/Sao_Paulo**, com
`catchup=False` e duas novas tentativas em caso de falha. O ambiente precisa estar
ligado para executar nesse horário. A DAG transforma os dados que já estão na Raw;
a geração de cadastros acontece na preparação inicial ou pelo comando abaixo.

## Carga e execução manual

Para acrescentar outro lote fictício:

```bash
docker compose exec airflow-scheduler /opt/pipeline-venv/bin/python /opt/project/scripts/generate_data.py --rows 100 --seed 43
```

Depois, trigge a DAG novamente. Também é possível executar o dbt diretamente,
com os serviços iniciados e a DAG ociosa:

```bash
docker compose exec airflow-scheduler /opt/pipeline-venv/bin/dbt run
```

## Consulta dos resultados

No DBeaver, crie uma conexão PostgreSQL com os dados abaixo:

| Campo | Valor |
|---|---|
| Host | `127.0.0.1` |
| Porta | `5433`, ou o valor de `POSTGRES_PORT` |
| Banco | `xptoz` |
| Usuário | `xptoz` |
| Senha | `XPTOZ_DB_PASSWORD` do `.env` |

A porta `5433` é usada no computador. Dentro do Docker, a conexão é com
`postgres:5432`, conforme `dbt/profiles.yml`. O Compose passa a senha ao dbt pela
variável `DBT_ENV_SECRET_DB_PASSWORD`.

```sql
SELECT dominio_email, total_registros, created_at, updated_at
FROM analytics_marts.mart_users_por_dominio
ORDER BY total_registros DESC, dominio_email;
```

## Encerramento e manutenção

Para parar mantendo os dados e o histórico do Airflow:

```bash
docker compose down
```

Para iniciar novamente, use `docker compose up -d --wait`. Se houver alteração
no código, use `docker compose up -d --build --wait` para reconstruir a imagem.

Para apagar os dados e o histórico e começar de novo:

```bash
docker compose down --volumes
```

Esse comando remove os volumes do projeto, incluindo logs e autenticação. Para
gerar credenciais novas, remova também o `.env` antes de repetir a configuração.
Alterar somente a senha no `.env` não troca a senha de um banco já existente.

O [roteiro do vídeo](docs/roteiro_loom.md) reúne os pontos da demonstração.
