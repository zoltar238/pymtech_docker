import zipfile
from pathlib import Path

files = {
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15
    container_name: postgres
    environment:
      POSTGRES_DB: odoo
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - '5433:5432'
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata
    restart: always

  odoo:
    build:
      context: ./odoo
      dockerfile: Dockerfile
    container_name: odoo
    depends_on:
      - db
    ports:
      - "8069:8069"
    tty: true
    volumes:
      - ./odoo/addons:/mnt/extra-addons
      - ./odoo/config:/etc/odoo
      - ./odoo/log:/var/log/odoo/
      - odoo-web-data:/var/lib/odoo
    entrypoint: ["/wait-for-db.sh"]
    command: [
      "odoo",
      "--db_host=db",
      "--db_port=5432",
      "--db_user=odoo",
      "--db_password=odoo"
    ]
    restart: always

volumes:
  odoo-web-data:
    name: odoo-18-docker_odoo-web-data
  odoo-db-data:
    name: odoo-18-docker_odoo-db-data
""",
    "odoo/Dockerfile": """FROM odoo:18.0

USER root

RUN apt-get update && apt-get install -y python3-pip && \\
    pip3 install python-barcode && \\
    apt-get clean

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

USER odoo
""",
    "odoo/wait-for-db.sh": """#!/bin/bash

echo "Esperando a que la base de datos esté disponible..."

until pg_isready -h db -p 5432 -U odoo > /dev/null 2>&1; do
  sleep 2
done

echo "Base de datos disponible, iniciando Odoo..."

exec "$@"
"""
}

zip_path = Path("odoo_docker_setup.zip")
with zipfile.ZipFile(zip_path, "w") as zf:
    for path, content in files.items():
        zf.writestr(path, content)

print(f"Archivo generado: {zip_path.resolve()}")
