#!/bin/bash

echo "Esperando a que la base de datos esté disponible..."

until pg_isready -h db -p 5432 -U odoo > /dev/null 2>&1; do
  sleep 2
done

echo "Base de datos disponible, iniciando Odoo..."

exec "$@"
