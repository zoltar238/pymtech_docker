ARG ODOO_VERSION=18
FROM odoo:${ODOO_VERSION}

# Change user to root to install needed dependencies
USER root

# Get requirements.txt route
ARG ODOO_REQUIREMENTS
COPY addons/requirements.txt requirements.txt


# Install pip, mandatory packages, and specific odoo python requirements
ARG ODOO_VERSION_2
ARG OPTIONAL_WHISPER
RUN apt-get update && \
    apt-get install -y \
        python3-pip \
        fonts-liberation \
        wget xfonts-75dpi \
        vim \
    && \
    if [ "$ODOO_VERSION_2" = "16" ]; then \
        pip3 install --no-cache-dir "Werkzeug==2.0.2" &&\
        pip3 install python-barcode gevent gevent-websocket jingtrang; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            pip3 install openai && \
            apt-get install ffmpeg -y; \
        fi; \
    else \
        export PIP_BREAK_SYSTEM_PACKAGES="--break-system-packages" && \
        pip3 install python-barcode gevent gevent-websocket jingtrang --break-system-packages; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            apt install python3-openai -y && \
            apt-get install ffmpeg -y; \
        fi; \
    fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN chmod -R 777 /var/log/odoo

RUN chmod -R 777 /etc/odoo

ENV ODOO_VERSION_2=${ODOO_VERSION_2}

COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

# Switch back to odoo user
USER odoo

ENTRYPOINT ["/custom-entrypoint.sh"]
CMD ["odoo"]
