#!/bin/bash

set -e

echo "Custom entrypoint executing"

# Check if extra-addons exists and has requirements.txt
if [ -f /mnt/extra-addons/requirements.txt ]; then
    echo "Installing dependencies from requirements.txt"
    # Usar --break-system-packages solo para Odoo 18
    if [ "$ODOO_VERSION_2" = "18" ]; then
        echo "Using --break-system-packages for Odoo 18"
        pip3 install --break-system-packages -r /mnt/extra-addons/requirements.txt
    else
        pip3 install -r /mnt/extra-addons/requirements.txt
    fi
    echo "Dependencies installed successfully"
else
    echo "No requirements.txt found in /mnt/extra-addons"
fi

# List addons for debugging
echo "Available addons in /mnt/extra-addons:"
ls -la /mnt/extra-addons/ 2>/dev/null || echo "Directory /mnt/extra-addons not found"

# Execute the original Odoo entrypoint
echo "Starting Odoo..."
exec /entrypoint.sh "$@"
