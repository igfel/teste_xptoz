FROM apache/airflow:3.3.2-python3.12@sha256:9df9c8be4096b9cc626bd7cb1f2b8c712eef66c59c615f8c7e6200871ca10bd1

USER root
RUN python -m venv /opt/pipeline-venv \
    && mkdir -p /opt/airflow/auth /opt/airflow/artifacts \
    && chown -R airflow:0 /opt/pipeline-venv /opt/airflow/auth /opt/airflow/artifacts \
    && chmod 2775 /opt/airflow/auth /opt/airflow/artifacts

USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN /opt/pipeline-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=airflow:0 scripts/ /opt/project/scripts/
COPY --chown=airflow:0 dbt/ /opt/project/dbt/
COPY --chown=airflow:0 airflow/dags/ /opt/airflow/dags/
WORKDIR /opt/project/dbt
