# 🐋 Odoo Docker Deployment

Este proyecto proporciona una configuración Docker para el despliegue automatizado de Odoo, diseñado para facilitar
tanto entornos de desarrollo como de producción.

## 📋 Requisitos Previos

- Docker Engine (20.10.0 o superior)
- Docker Compose (2.0.0 o superior)
- Git
- Libreria de python `dotenv`

## 🚀 Inicio Rápido

1. Clona el repositorio:
   `git clone https://github.com/zoltar238/pymtech_docker.git`

2. Crea la red externa de traefik:
   `docker network create traefik`. La red externa de traefik deberá existir tanto
   en entornos de producción como de desarrollo

3. Determina el entorno:
    1. En entornos de producción será necesario el contenedor de "traefik" para el proxy inverso.
       Dentro de la carpeta de traefik, con la red externa creada, ejecuta `docker compose up -d`
       para iniciar el servicio y `docker compose down` para detenerlo
    2. En entornos de desarrollo el contenedor de traefik no es necesario y se puede eliminar

4. Accede a la carpeta del contenedor de odoo y modifica los parámetros del servicio
   contenidos en el archivo: `.env`

5. Lanza el servicio de Odoo desde la carpeta del contenedor ejecutando: `python3 deploy.py`
   Usa el mismo comando para reiniciar los contenedores de odoo. Usa `docker compose down` en caso
   de que sea necesario detener el servicio de odoo

## ⚙️ Configuración

## ⚙️ Configuración Detallada del Archivo .env

### Configuración Principal

| Variable             | Descripción                                                                             | Valores Posibles                 | Valor por Defecto |
|----------------------|-----------------------------------------------------------------------------------------|----------------------------------|-------------------|
| COMPOSE_PROJECT_NAME | Nombre del proyecto. Crucial para separar datos entre instancias y nombrar contenedores | Texto libre (ej: client_name_18) | example_name      |
| DEPLOYMENT_TARGET    | Define el entorno de despliegue                                                         | dev/prod                         | dev               |
| SCRIPT_OUTPUT        | Nivel de detalle en la salida del script deploy.py                                      | verbose/silent                   | verbose           |

### Versiones y Contenedores

| Variable         | Descripción                | Valor por Defecto |
|------------------|----------------------------|-------------------|
| ODOO_VERSION     | Versión de Odoo a utilizar | 18                |
| POSTGRES_VERSION | Versión de PostgreSQL      | 15                |

### Red y Conectividad

| Variable           | Descripción                                       | Valor por Defecto |
|--------------------|---------------------------------------------------|-------------------|
| DOMAIN             | Dominio para el servicio (ej: example.loxika.com) | vacío             |
| ODOO_EXPOSED_PORT  | Puerto externo para acceder a Odoo                | 8075              |
| ODOO_INTERNAL_PORT | Puerto interno del contenedor                     | 8069              |

### Sistema de Archivos y Rutas

| Variable          | Descripción                           | Valor por Defecto       |
|-------------------|---------------------------------------|-------------------------|
| ODOO_LOG          | Ruta de los archivos de registro      | ./log                   |
| ODOO_CONFIG       | Ruta de los archivos de configuración | ./config                |
| ODOO_ADDONS       | Ruta de los módulos adicionales       | ./addons                |
| ODOO_REQUIREMENTS | Ruta del archivo requirements.txt     | addons/requirements.txt |

### Gestión de Módulos

| Variable             | Descripción                                       | Valores Posibles            | Valor por Defecto |
|----------------------|---------------------------------------------------|-----------------------------|-------------------|
| AUTO_INSTALL_MODULES | Instala módulos automáticamente al iniciar        | true/false                  | false             |
| AUTO_UPDATE_MODULES  | Actualiza módulos automáticamente al iniciar      | true/false                  | true              |
| UPDATE_MODULE_LIST   | Lista específica de módulos a actualizar          | nombres separados por comas | vacío             |
| FORCE_UPDATE         | Fuerza la actualización de módulos (¡Precaución!) | true/false                  | false             |

### Construcción y Desarrollo

| Variable      | Descripción                                 | Valores Posibles | Valor por Defecto |
|---------------|---------------------------------------------|------------------|-------------------|
| FORCE_REBUILD | Reconstruye la imagen Docker en cada inicio | true/false       | false             |

### Características Opcionales

| Variable         | Descripción                      | Valores Posibles | Valor por Defecto |
|------------------|----------------------------------|------------------|-------------------|
| OPTIONAL_WHISPER | Habilita el soporte para Whisper | true/false       | true              |

### ⚠️ Notas Importantes

- El `COMPOSE_PROJECT_NAME` es obligatorio y crucial para el correcto funcionamiento del sistema
- Modificar `FORCE_UPDATE` puede causar problemas en la instalación de Odoo
- `UPDATE_MODULE_LIST` tiene prioridad sobre `AUTO_UPDATE_MODULES`
- Asegúrate de que `ODOO_EXPOSED_PORT` no esté siendo utilizado por otra aplicación
- Asegurarse de que la carpeta de `logs` y `addons` dentro de odoo tienen permisos de escritura
- En caso de errores con redes, eliminar la red mencionada en el error de docker con `docker network rm <nombre_red>`

## 📁 Estructura de Directorios de ejemplo

Aquí se muestra una estructura de directorios de ejemplo, centrándose solo en aquellos archivos importantes para el
funcionamiento del proyecto:

<pre>
ruta_de_los_contenedores/
    ├── odoo_empresa_1
    │ ├── addons
    │ │ └── requirements.txt
    │ │ ├── modulo1
    │ │ └── modulo2
    │ ├── config
    │ │ └── odoo.conf
    │ ├── deploy.py
    │ ├── docker-compose.yml
    │ ├── log
    │ │ └── odoo-server.log
    │ ├── odoo.Dockerfile
    └── traefik
      └── docker-compose.yml
</pre>