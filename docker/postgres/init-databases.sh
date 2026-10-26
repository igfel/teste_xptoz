#!/usr/bin/env bash
set -euo pipefail

# O psql lê as senhas das variáveis de ambiente.
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 --quiet <<'SQL'
\getenv xptoz_password XPTOZ_DB_PASSWORD
\getenv airflow_password AIRFLOW_DB_PASSWORD
SELECT format('CREATE ROLE xptoz LOGIN PASSWORD %L', :'xptoz_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'xptoz') \gexec
SELECT format('CREATE ROLE airflow LOGIN PASSWORD %L', :'airflow_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow') \gexec
SELECT 'CREATE DATABASE xptoz OWNER xptoz'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'xptoz') \gexec
SELECT 'CREATE DATABASE airflow OWNER airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow') \gexec
REVOKE CONNECT ON DATABASE xptoz FROM PUBLIC;
REVOKE CONNECT ON DATABASE airflow FROM PUBLIC;
SQL
