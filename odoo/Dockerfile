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
ARG ODOO_VERSION
ENV PIP_ARGS=""
RUN if [ "$ODOO_VERSION" = "18" ]; then \
        echo "export PIP_ARGS='--break-system-packages'" >> /etc/profile.d/pip.sh; \
    fi

# Install Odoo Python requirements
COPY ../odoo/requirements.txt /tmp/odoo-requirements.txt
RUN . /etc/profile.d/pip.sh 2>/dev/null || true && \
    pip install $PIP_ARGS -r /tmp/odoo-requirements.txt

# Install Werkzeug for Odoo 16
ARG ODOO_VERSION
RUN if [ "$ODOO_VERSION" = "16" ]; then \
        pip3 install --no-cache-dir "Werkzeug==2.0.2"; \
    fi

# Install addon requirements
COPY ../addons/requirements.txt /tmp/addons-requirements.txt
RUN . /etc/profile.d/pip.sh 2>/dev/null || true && \
    pip install $PIP_ARGS -r /tmp/addons-requirements.txt

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
