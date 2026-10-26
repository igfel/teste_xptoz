import base64
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def create_env(root: Path = ROOT) -> bool:
    destination = root / ".env"
    if destination.exists():
        return False
    content = (root / ".env.example").read_text(encoding="utf-8")
    lines = []
    for line in content.splitlines():
        if line.endswith("=CHANGE_ME"):
            key = line.split("=", 1)[0]
            value = (
                base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
                if key == "AIRFLOW_FERNET_KEY"
                else secrets.token_hex(32)
            )
            line = f"{key}={value}"
        elif line.startswith("AIRFLOW_UID=") and hasattr(os, "getuid"):
            uid = os.getuid() or root.stat().st_uid or 50000
            line = f"AIRFLOW_UID={uid}"
        lines.append(line)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines) + "\n")
    if hasattr(os, "getuid") and os.getuid() == 0:
        # Se rodar como root no Docker, devolve o arquivo ao dono da pasta.
        owner = root.stat()
        os.chown(destination, owner.st_uid, owner.st_gid)
    return True


if __name__ == "__main__":
    print(
        ".env criado; credenciais mantidas no arquivo local."
        if create_env()
        else ".env preservado."
    )
