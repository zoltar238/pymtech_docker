ARG ODOO_VERSION=18
FROM odoo:${ODOO_VERSION}

# Change user to root to install needed dependencies
USER root

# Get requirements.txt route
ARG ODOO_REQUIREMENTS
COPY ${ODOO_REQUIREMENTS} requirements.txt


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
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb && \
    apt-get install -f && \
    if [ "$ODOO_VERSION_2" = "16" ]; then \
        pip3 install python-barcode gevent gevent-websocket && \
        pip3 install -r requirements.txt; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            pip3 install openai && \
            apt-get install ffmpeg -y; \
        fi; \
    else \
        pip3 install python-barcode gevent gevent-websocket --break-system-packages && \
        pip3 install -r requirements.txt --break-system-packages; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            apt install python3-openai -y && \
            apt-get install ffmpeg -y; \
        fi; \
    fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN chmod 777 /var/log/odoo

# Switch back to odoo user
USER odoo