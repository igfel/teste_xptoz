import json
import os
from pathlib import Path


def initialize_auth() -> None:
    username = os.environ.get("AIRFLOW_ADMIN_USER", "admin")
    if not username or any(character in username for character in ":,\n\r"):
        raise ValueError("AIRFLOW_ADMIN_USER invalido.")
    password = os.environ["AIRFLOW_ADMIN_PASSWORD"]
    if not password or password == "CHANGE_ME":
        raise ValueError("Configure uma senha local antes de iniciar o Airflow.")
    path = Path(os.environ["AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump({username: password}, output)
    temporary.replace(path)
    path.chmod(0o600)


if __name__ == "__main__":
    initialize_auth()
    print("Autenticacao local preparada.")
