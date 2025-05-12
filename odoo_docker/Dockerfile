FROM odoo:18.0

# Cambiar a root para instalar paquetes del sistema
USER root

# Instalar pip y el módulo python-barcode
RUN apt-get update && apt-get install -y python3-pip \
 && pip install python-barcode --break-system-packages \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Volver al usuario por defecto de Odoo
USER odoo
