import argparse
import json
import logging
import os
from contextlib import closing
from dataclasses import asdict, dataclass

import psycopg2
from faker import Faker

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadResult:
    attempted: int
    inserted: int
    ignored: int


def database_config() -> dict:
    required = ("PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError("Variaveis obrigatorias ausentes: " + ", ".join(missing))
    return {
        "host": os.environ["PGHOST"],
        "port": int(os.environ.get("PGPORT", "5432")),
        "dbname": os.environ["PGDATABASE"],
        "user": os.environ["PGUSER"],
        "password": os.environ["PGPASSWORD"],
        "connect_timeout": 10,
        "application_name": "xptoz_generate_data",
    }


def conectar_banco():
    return psycopg2.connect(**database_config())


def criar_tabela(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_info (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                idade INT,
                cidade VARCHAR(100)
            );
        """)


def gerar_dados(qtd: int = 1000, seed: int | None = None) -> list[tuple]:
    if qtd < 0:
        raise ValueError("A quantidade deve ser maior ou igual a zero.")
    fake = Faker("pt_BR")
    if seed is not None:
        fake.seed_instance(seed)
    return [
        (fake.name(), fake.email(), fake.random_int(min=18, max=80), fake.city())
        for _ in range(qtd)
    ]


def inserir_dados(conn, dados: list[tuple]) -> LoadResult:
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO users_info (nome, email, idade, cidade)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING;
            """,
            dados,
        )
        inserted = max(cursor.rowcount, 0)
    return LoadResult(len(dados), inserted, len(dados) - inserted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera e carrega os cadastros ficticios do case.")
    parser.add_argument("--rows", type=int, default=os.environ.get("DATA_ROWS", "1000"))
    parser.add_argument("--seed", type=int, default=os.environ.get("FAKER_SEED", "42"))
    args = parser.parse_args(argv)
    try:
        dados = gerar_dados(args.rows, args.seed)
        with closing(conectar_banco()) as conn, conn:
            criar_tabela(conn)
            result = inserir_dados(conn, dados)
        print(json.dumps(asdict(result)))
        return 0
    except (ValueError, psycopg2.Error) as exc:
        # A mensagem do driver pode incluir dados da conexão.
        LOGGER.error(
            "Carga cancelada; nenhuma transacao parcial confirmada (%s).", type(exc).__name__
        )
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
