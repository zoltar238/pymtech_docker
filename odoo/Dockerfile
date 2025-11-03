ARG ODOO_VERSION=18
FROM odoo:${ODOO_VERSION}

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
        python3-pip \
        fonts-liberation \
        wget xfonts-75dpi \
        vim \
    && rm -rf /var/lib/apt/lists/*

# Set pip arguments based on Odoo version
# Set pip flags globally for Odoo 18
ARG ODOO_VERSION
ENV PIP_BREAK_SYSTEM_PACKAGES=${ODOO_VERSION:+1}


# Install Odoo Python requirements
COPY ../odoo/requirements.txt /tmp/odoo-requirements.txt
RUN pip install --ignore-installed -r /tmp/odoo-requirements.txt

# Install dependencies that are only needed on version 16
ARG ODOO_VERSION
RUN if [ "$ODOO_VERSION" = "16" ]; then \
        pip3 install --no-cache-dir "Werkzeug==2.0.2" lxml-html-clean; \
    fi

# Install addon requirements
COPY ../addons/requirements.txt /tmp/addons-requirements.txt
RUN pip install --ignore-installed -r /tmp/addons-requirements.txt

# Install whisper (optional)
ARG OPTIONAL_WHISPER
ARG ODOO_VERSION
RUN if [ "$ODOO_VERSION" = "18" ] && [ "$OPTIONAL_WHISPER" ]; then \
        apt-get update && \
        apt-get install -y python3-openai ffmpeg && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Set permissions
RUN chmod -R 777 /var/log/odoo /etc/odoo /var/lib/odoo

USER odoo
