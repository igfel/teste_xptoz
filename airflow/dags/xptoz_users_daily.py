from datetime import timedelta

import pendulum

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(
    dag_id="xptoz_users",
    description="consolida cadastros por dominio de email.",
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Sao_Paulo"),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(minutes=20),
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
    tags=["xptoz", "dbt", "daily"],
) as dag:
    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command=(
            "/opt/pipeline-venv/bin/dbt run "
            "--project-dir /opt/project/dbt --profiles-dir /opt/project/dbt"
        ),
        env={
            "DBT_TARGET_PATH": "/opt/airflow/artifacts/{{ run_id | replace('/', '_') }}",
            "DBT_LOG_PATH": "/opt/airflow/logs/dbt/{{ run_id | replace('/', '_') }}",
        },
        append_env=True,
        execution_timeout=timedelta(minutes=10),
    )
