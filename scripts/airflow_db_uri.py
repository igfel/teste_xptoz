import os
from urllib.parse import quote


def database_uri() -> str:
    password = quote(os.environ["AIRFLOW_DB_PASSWORD"], safe="")
    return f"postgresql+psycopg2://airflow:{password}@postgres:5432/airflow"


if __name__ == "__main__":
    print(database_uri(), end="")
