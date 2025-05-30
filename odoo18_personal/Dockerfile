ARG ODOO_VERSION=18
FROM odoo:${ODOO_VERSION}

# Change user to root to install needed dependencies
USER root

# Get requirements.txt route
ARG ODOO_REQUIREMENTS
COPY ${ODOO_REQUIREMENTS} requirements.txt


# Install pip, mandatory packages, and specific odoo python requirements
ARG ODOO_VERSION
RUN apt-get update && apt-get install -y python3-pip && \
    if [ "$ODOO_VERSION" = "16" ]; then \
        pip3 install python-barcode && \
        pip3 install -r requirements.txt; \
    else \
        pip3 install python-barcode --break-system-packages && \
        pip3 install -r requirements.txt --break-system-packages; \
    fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to odoo user
USER odoo