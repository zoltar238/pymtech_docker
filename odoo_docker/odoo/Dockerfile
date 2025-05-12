FROM odoo:18.0

USER root

# Instalar pip y entorno virtual, e instalar python-barcode sin romper el sistema
RUN apt-get update && apt-get install -y python3-pip python3-venv python3-psycopg2 && \
    python3 -m venv /opt/odoo-venv && \
    /opt/odoo-venv/bin/pip install psycopg2-binary python-barcode && \
    apt-get clean

# Copiar el script y darle permisos de ejecución
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Agregar el entorno virtual al PATH
ENV PATH="/opt/odoo-venv/bin:$PATH"

USER odoo
