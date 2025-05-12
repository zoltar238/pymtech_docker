FROM odoo:18.0

USER root

RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install python-barcode && \
    apt-get clean

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

USER odoo
