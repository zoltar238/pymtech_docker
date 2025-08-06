# 🐋 Odoo Docker Deployment

Este proyecto proporciona una configuración Docker para el despliegue automatizado de Odoo, diseñado para facilitar tanto entornos de desarrollo como de producción.

## 📋 Requisitos Previos
- Docker Engine (20.10.0 o superior)
- Docker Compose (2.0.0 o superior)
- Git
- Libreria de python "dotenv"

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

### Variables Principales
| Variable | Descripción | Opciones | Ejemplo |
|----------|-------------|----------|----------|
| COMPOSE_PROJECT_NAME | Nombre del proyecto (¡Obligatorio!) | texto libre | personal_18 |
| DEPLOYMENT_TARGET | Entorno de despliegue | dev/prod | dev |
| SCRIPT_OUTPUT | Nivel de detalle en logs | verbose/silent | verbose |

### Paquetes Opcionales
| Variable | Descripción | Opciones |
|----------|-------------|----------|
| OPTIONAL_WHISPER | Habilita soporte para Whisper | true/false |

### Automatización de Módulos
| Variable | Descripción | Opciones |
|----------|-------------|----------|
| AUTO_INSTALL_MODULES | Instalación automática | true/false |
| AUTO_UPDATE_MODULES | Actualización automática | true/false |
| UPDATE_MODULE_LIST | Lista de módulos a actualizar | nombres separados por comas |
| FORCE_UPDATE | Forzar actualización (¡Precaución!) | true/false |

### Versiones
| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| ODOO_VERSION | Versión de Odoo | 18 |
| POSTGRES_VERSION | Versión de PostgreSQL | 15 |

### Configuración de Red
| Variable | Descripción | Ejemplo |
|----------|-------------|----------|
| DOMAIN | Dominio para el servicio | gestion.empresa.com |
| ODOO_EXPOSED_PORT | Puerto expuesto | 8070 |
| ODOO_INTERNAL_PORT | Puerto interno | 8069 |

## 📁 Estructura de Directorios
