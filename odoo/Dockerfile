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
    && \
    if [ "$ODOO_VERSION_2" = "16" ]; then \
        pip3 install python-barcode gevent gevent-websocket && \
        pip3 install -r requirements.txt; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            pip3 install whisper && \
            apt-get install ffmpeg -y; \
        fi; \
    else \
        pip3 install python-barcode gevent gevent-websocket --break-system-packages && \
        pip3 install -r requirements.txt --break-system-packages; \
        if [ "$OPTIONAL_WHISPER" = "true" ]; then \
            pip3 install whisper --break-system-packages && \
            apt-get install ffmpeg -y; \
        fi; \
    fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to odoo user
USER odoo