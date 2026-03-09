=====================================================
PORTAFOLIO FINANCIERO — BACKEND FLASK + DOCKER
=====================================================

Aplicación de portafolio financiero con backend en Flask, base de datos MySQL y despliegue mediante Docker Compose.[web:137][web:131]  
Incluye autenticación con bcrypt, sesiones seguras, generación de token de API, CORS y cabeceras de seguridad con Flask‑Talisman.[web:146][web:150][web:148][web:151]

=====================================================
ESTRUCTURA DEL PROYECTO
=====================================================

proyecto-1/
├── app.py                           ← Backend Flask (API REST)
├── index.html                       ← Frontend estático
├── docker-compose.yml               ← Orquestación Docker Compose
├── Dockerfile                       ← Imagen del backend
├── requirements.txt                 ← Dependencias Python
├── portafolio_db.sql                ← Script inicial de base de datos
├── README.md                        ← Este documento
└── .env                             ← Variables de entorno (no subir a Git)

=====================================================
TECNOLOGÍAS UTILIZADAS
=====================================================

- **Flask** como framework web para Python.
- **MySQL** como base de datos relacional.
- **mysql-connector-python** para conectar Flask con MySQL.
- **bcrypt** para hash y verificación de contraseñas.
- **Flask-CORS** para configurar CORS entre frontend y backend.
- **Flask-Talisman** para añadir cabeceras de seguridad (CSP, cookies seguras, etc.).
- **Docker** y **Docker Compose** para desplegar backend y base de datos en contenedores.
- **Sesiones de Flask** para autenticación vía cookie.
- **Tokens de API** generados con `secrets.token_hex(32)` y almacenados en la tabla `usuarios`.

=====================================================
VARIABLES DE ENTORNO (.env)
=====================================================

En la raíz del proyecto crea un archivo `.env`:

DB_HOST=db
DB_PORT=3306
DB_USER=appuser
DB_PASSWORD=apppass
DB_NAME=portafolio_financiero
FLASK_SECRET_KEY=portafolio_super_secret_2025
FLASK_DEBUG=false

python
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "portafolio_financiero"),
    "port":     int(os.getenv("DB_PORT", "3306")),
}
=====================================================
BASE DE DATOS (MySQL)
Levanta los contenedores (ver siguiente sección).

bash
docker exec -i NOMBRE_CONTENEDOR_DB \
  mysql -u root -p portafolio_financiero < portafolio_db.sql
Asegúrate de que la tabla usuarios tiene la columna de token:

sql
ALTER TABLE usuarios
  ADD COLUMN api_token VARCHAR(255) NULL;
Tablas usadas (resumen):

usuarios (id, nombre, email, password_hash, rol, activo, api_token)

portafolios

activos

transacciones

precios_historicos

alertas

=====================================================
DESPLIEGUE CON DOCKER COMPOSE
Desde la carpeta donde está docker-compose.yml:

bash
docker compose down
docker compose up --build
# o en segundo plano:
docker compose up --build -d
Ver logs:

bash
docker compose logs -f
Deberías ver algo como:

text
=======================================================
  PORTAFOLIO FINANCIERO - BACKEND FLASK
  Modo debug: True/False
  Servidor: http://localhost:5000
=======================================================
Servicios típicos en docker-compose.yml:

db → MySQL (puerto interno 3306).

backend → Flask, expuesto en el puerto 5000 del host.

=====================================================
CONFIGURACIÓN DE SEGURIDAD
En app.py se han aplicado varias medidas:

Cookies de sesión:

SESSION_COOKIE_HTTPONLY=True (no accesible desde JS).

SESSION_COOKIE_SAMESITE="Lax" (mitiga CSRF).

SESSION_COOKIE_SECURE=False en desarrollo (True en producción con HTTPS).

Flask-Talisman:

Configura Content-Security-Policy (CSP) para limitar scripts, estilos, imágenes y fuentes.

Configura cabeceras de seguridad comunes.

Flask-CORS:

Permite orígenes http://localhost:5000, http://127.0.0.1:5000 y null con credenciales.

=====================================================
AUTENTICACIÓN (SESIONES + TOKEN API)
Registro de usuario
POST /api/register

Body JSON:

json
{
  "nombre": "Usuario Demo",
  "email": "usuario@example.com",
  "password": "contraseña_segura"
}
Valida longitud mínima de la contraseña (8 caracteres).

Valida formato básico del email.

Hashea la contraseña con bcrypt.hashpw(...).decode().

Crea el usuario con rol user y un portafolio por defecto: "Mi Portafolio".

Login
POST /api/login

Body JSON:

json
{
  "email": "usuario@example.com",
  "password": "contraseña_segura"
}
Flujo:

Recupera el usuario activo desde MySQL.

Verifica la contraseña con bcrypt.checkpw.

Guarda en la sesión:

session["user_id"]

session["user_name"]

session["user_role"]

Genera un token de API:

python
import secrets

def generate_api_token():
    return secrets.token_hex(32)
Actualiza usuarios.api_token con ese token.

Devuelve en la respuesta JSON:

json
{
  "status": "success",
  "message": "Login exitoso",
  "data": {
    "id": 1,
    "nombre": "Usuario Demo",
    "email": "usuario@example.com",
    "rol": "user",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
Logout y usuario actual
POST /api/logout → Limpia la sesión.

GET /api/me → Devuelve id, nombre y rol del usuario logueado.

Decoradores:

@login_required → requiere session["user_id"].

@admin_required → requiere sesión y session["user_role"] == "admin".

(Para APIs externas puedes añadir en el futuro un @token_required que valide Authorization: Bearer <token> contra usuarios.api_token.)

=====================================================
FRONTEND

El frontend espera que el backend esté en http://localhost:5000.

=====================================================
ENDPOINTS DE LA API
Autenticación

Método	Endpoint	Descripción
POST	/api/register	Registrar usuario
POST	/api/login	Iniciar sesión (sesión + token)
POST	/api/logout	Cerrar sesión
GET	/api/me	Datos del usuario actual
Administración

Método	Endpoint	Descripción
GET	/api/admin/usuarios	Listar usuarios (solo admin)
Portafolios

Método	Endpoint	Descripción
GET	/api/portafolios	Listar portafolios del usuario
POST	/api/portafolios	Crear portafolio
DELETE	/api/portafolios/:id	Eliminar portafolio
Activos

Método	Endpoint	Descripción
GET	/api/activos	Listar activos (con filtro tipo)
POST	/api/activos	Crear activo (solo admin)
Transacciones

Método	Endpoint	Descripción
GET	/api/transacciones	Listar transacciones (por portafolio_id)
POST	/api/transacciones	Crear transacción
DELETE	/api/transacciones/:id	Eliminar transacción
Resumen y estadísticas

Método	Endpoint	Descripción
GET	/api/resumen/:portafolio_id	Resumen de posiciones, valor y PnL
GET	/api/estadisticas/:id	Estadísticas avanzadas del portafolio
Precios históricos

Método	Endpoint	Descripción
GET	/api/precios	Listar precios históricos (activo_id)
POST	/api/precios	Insertar/actualizar precio histórico
Alertas

Método	Endpoint	Descripción
GET	/api/alertas	Listar alertas del usuario
POST	/api/alertas	Crear alerta
DELETE	/api/alertas/:id	Eliminar alerta
=====================================================
CÓMO EJECUTAR SIN DOCKER (OPCIONAL)
Crear entorno virtual:

bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
Instalar dependencias:

bash
pip install -r requirements.txt
Exportar variables de entorno (DB_*, FLASK_*) apuntando a tu MySQL local.

Ejecutar:

bash
python app.py
Servidor disponible en http://localhost:5000.

=====================================================
NOTAS FINALES
En producción:

Usar HTTPS y SESSION_COOKIE_SECURE=True.

Revisar y endurecer la política CSP de Talisman.

Configurar contraseñas y secretos vía variables de entorno seguras.