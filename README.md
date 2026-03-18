# 📊 Portafolio Pro — Práctica SecDevOps

> Aplicación de gestión de portafolio financiero desarrollada como práctica del ciclo **SecDevOps**.  
> Backend en **Flask (Python 3.12)**, base de datos **MySQL 8.0**, frontend en **HTML/JS** estático (SPA),  
> desplegado íntegramente mediante **Docker Compose** y con pipeline de CI/CD en **GitHub Actions**.

---

## Índice

1. [Descripción del proyecto](#descripción-del-proyecto)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Tecnologías utilizadas](#tecnologías-utilizadas)
4. [Entorno de desarrollo — Docker](#entorno-de-desarrollo--docker)
5. [Entorno virtual Python (alternativa)](#entorno-virtual-python-alternativa)
6. [Base de datos](#base-de-datos)
7. [Autenticación y autorización](#autenticación-y-autorización)
8. [Variables de entorno](#variables-de-entorno)
9. [Endpoints de la API](#endpoints-de-la-api)
10. [Pruebas](#pruebas)
11. [CI/CD con GitHub Actions](#cicd-con-github-actions)
12. [Gestión de versiones con Git](#gestión-de-versiones-con-git)
13. [Seguridad aplicada — OWASP](#seguridad-aplicada--owasp)
14. [Notas para producción](#notas-para-producción)

---

##  Descripción del proyecto

**Portafolio Pro** es una aplicación web que permite a inversores gestionar sus carteras financieras:

- Registrar **compras, ventas y dividendos** de acciones, ETFs, criptomonedas, bonos y materias primas
- Ver el **resumen en tiempo real** de posiciones, valor de mercado, coste total y P&L (ganancia/pérdida)
- Visualizar **gráficas de distribución** por tipo de activo y por sector
- Configurar **alertas de precio** sobre cualquier activo del catálogo
- Gestionar múltiples **portafolios independientes** por usuario

El objetivo principal de la práctica **no es la funcionalidad financiera** sino demostrar un ciclo completo de SecDevOps:  
contenedores → entornos virtuales → autenticación segura → API REST → OWASP → tests → CI/CD → Git.

---

##  Estructura del proyecto

```
portafolio-pro/
├── app.py                          # Backend Flask — API REST completa
├── index.html                      # Frontend estático (SPA — Single Page App)
├── docker-compose.yml              # Orquestación de servicios Docker
├── Dockerfile                      # Imagen Docker del backend Flask
├── requirements.txt                # Dependencias Python fijadas con versión
├── portfolio_db.sql                # Script SQL de inicialización de la BD
├── .gitignore                      # Ficheros y carpetas excluidos de Git
├── .env                            # Variables de entorno locales (NO subir a Git)
├── README.md                       # Este documento
├── OWASP.md                        # Análisis de seguridad OWASP Top 10
├── Portafolio-Pro.postman_collection.json  # Colección Postman para pruebas manuales
├── .github/
│   └── workflows/
│       └── ci.yml                  # Pipeline de CI/CD con GitHub Actions
└── test/
    ├── test_unit.py                # Tests unitarios (pytest)
    └── test_integration.py         # Tests de integración (pytest)
```

---

##  Tecnologías utilizadas

| Capa | Tecnología | Versión | Función |
|------|-----------|---------|---------|
| Backend | Flask | 3.x | Framework web Python — API REST + servidor SPA |
| Base de datos | MySQL | 8.0 | Persistencia relacional de datos financieros |
| Conector BD | mysql-connector-python | latest | Conexión Flask ↔ MySQL con queries parametrizadas |
| Hash contraseñas | bcrypt | latest | Almacenamiento seguro de passwords con salt |
| Cabeceras HTTP | Flask-Talisman | latest | CSP, HSTS, X-Frame-Options, X-Content-Type |
| CORS | Flask-CORS | latest | Control de orígenes cruzados entre frontend y API |
| Contenedores | Docker + Compose | latest | Despliegue reproducible y aislado |
| CI/CD | GitHub Actions | — | Pipeline automático de tests en cada push |
| Tests | pytest | latest | Tests unitarios e integración |
| Pruebas manuales | Postman | — | Colección de pruebas de todos los endpoints |
| Frontend | HTML5 + Vanilla JS | — | SPA sin framework, comunicación con la API via fetch |
| Gráficas | Chart.js | 4.4.0 | Doughnut charts de distribución de portafolio |

---

##  Entorno de desarrollo — Docker

**Opción utilizada: entorno en contenedores Docker Compose.**  
Todo el stack (backend + base de datos) se levanta con un único comando, aislado del sistema anfitrión.

### Servicios en `docker-compose.yml`

| Servicio | Imagen | Puerto host | Puerto contenedor | Función |
|----------|--------|-------------|-------------------|---------|
| `db` | mysql:8.0 | 3307 | 3306 | Base de datos MySQL |
| `backend` | python:3.12-slim (build local) | 5000 | 5000 | API Flask + servidor SPA |

El servicio `backend` **espera a que `db` esté sano** antes de arrancar gracias al `healthcheck` de MySQL:

```yaml
depends_on:
  db:
    condition: service_healthy
```

### Comandos principales

```bash
# Levantar todo el stack (primera vez o tras cambios)
docker compose up --build -d

# Ver logs en tiempo real
docker compose logs -f

# Parar y eliminar contenedores
docker compose down

# Parar y eliminar contenedores + volúmenes (borra la BD)
docker compose down -v

# Para entrar usaremos admin@demo.com y contraseña admin123 y tendremos rol ADMIN
+----+----------------------+-----------------------+-------+--------+
| id | nombre               | email                 | rol   | activo |
+----+----------------------+-----------------------+-------+--------+
|  1 | Usuario Demo         | demo@portafolio.com   | user  |      1 |
|  6 | ADMIN                | admin@gmail.com       | user  |      1 |
|  7 | Quico Alonso De Caso | quicoalonso@gmail.com | user  |      1 |
|  8 | Usuario Test         | testuser@example.com  | user  |      1 |
| 13 | Javier Trapero       | javitrap@gmail.com    | user  |      1 |
| 14 | Admin Demo           | admin@demo.com        | admin |      1 |

```

### Verificar que todo funciona

```bash
docker compose ps
```

Deberías ver ambos contenedores con estado `Up (healthy)`:

```
NAME                  STATUS
portafolio-db         Up (healthy)
portafolio-backend    Up
```

Y en los logs del backend:

```
═══════════════════════════════════════════════════
  PORTAFOLIO FINANCIERO - BACKEND FLASK
  Modo debug: False
  Servidor: http://localhost:5000
═══════════════════════════════════════════════════
```

##  Entorno virtual Python (alternativa sin Docker)

Si se prefiere ejecutar el backend directamente en la máquina sin Docker:

```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activar (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 2. Activar (Linux / macOS)
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (copiar y editar)
cp .env.example .env

# 5. Ejecutar el backend
python app.py
```


##  Base de datos

### Esquema de tablas (MySQL)

| Tabla | Descripción | Campos clave |
|-------|------------|--------------|
| `usuarios` | Usuarios registrados | `id`, `nombre`, `email`, `password_hash`, `rol`, `activo`, `api_token` |
| `portafolios` | Carteras de inversión por usuario | `id`, `usuario_id`, `nombre`, `moneda_base` |
| `activos` | Catálogo de instrumentos financieros | `id`, `ticker`, `nombre`, `tipo`, `sector`, `moneda` |
| `transacciones` | Compras, ventas y dividendos | `id`, `portafolio_id`, `activo_id`, `tipo`, `cantidad`, `precio_unitario`, `comision`, `fecha` |
| `precios_historicos` | Precios de cierre por activo y fecha | `activo_id`, `fecha`, `precio_cierre`, `volumen` |
| `alertas` | Alertas de precio por usuario | `id`, `usuario_id`, `activo_id`, `tipo`, `valor_referencia`, `activa` |

### Inicialización automática

Al levantar con Docker Compose, el fichero `portfolio_db.sql` se ejecuta automáticamente como script de inicialización gracias a:

```yaml
volumes:
  - ./portfolio_db.sql:/docker-entrypoint-initdb.d/init.sql
```

### Inicialización manual (sin Docker)

```bash
docker exec -i portafolio-db mysql -u root -prootpass portafoliofinanciero < portfolio_db.sql
```

---

##  Autenticación y autorización

### Dos tipos de usuario

| Rol | Permisos |
|-----|---------|
| `user` | Gestionar sus propios portafolios, transacciones, alertas y ver activos |
| `admin` | Todo lo anterior + ver todos los usuarios, crear activos, cargar precios históricos |

### Diferenciación visual del administrador

Cuando un usuario con rol `admin` inicia sesión, la interfaz cambia visualmente:
- El título del topbar muestra **⚙️ ADMIN — Dashboard**
- Aparece un badge **ADMIN** dorado junto al nombre en el sidebar
- El sidebar adopta un tono dorado/ámbar para distinguirlo del usuario normal

### Decoradores de seguridad en `app.py`

```python
def login_required(f):
    # Verifica que session['user_id'] existe antes de procesar la petición
    # Si no hay sesión → 401 Unauthorized

def admin_required(f):
    # Verifica sesión activa Y que session['user_role'] == 'admin'
    # Si es user normal → 403 Forbidden
```

### Flujo completo de autenticación

```
1. POST /api/register
   Body: { nombre, email, password }
   → Valida: email válido, contraseña ≥ 8 caracteres
   → Hashea password con bcrypt + salt aleatorio
   → Crea usuario con rol 'user' + portafolio 'Mi Portafolio' por defecto
   → Responde: { status: 'success', usuario_id: X }

2. POST /api/login
   Body: { email, password }
   → Busca usuario activo en BD por email
   → Verifica password con bcrypt.checkpw (tiempo constante)
   → Mensaje de error genérico si falla (no revela si el email existe)
   → Guarda en sesión: session['user_id'], session['user_name'], session['user_role']
   → Genera token API con secrets.token_hex(32) → 256 bits de entropía
   → Actualiza usuarios.api_token en BD
   → Responde: { id, nombre, email, rol, token }

3. GET /api/me
   → Devuelve datos del usuario autenticado desde la sesión
   → Usado por el frontend para restaurar sesión al recargar la página

4. POST /api/logout
   → session.clear() — invalida completamente la sesión
```

##  Endpoints de la API

Base URL: `http://localhost:5000/api`

### Autenticación (pública)

| Método | Endpoint | Descripción | Body requerido |
|--------|----------|-------------|----------------|
| `POST` | `/register` | Registrar nuevo usuario | `{ nombre, email, password }` |
| `POST` | `/login` | Iniciar sesión | `{ email, password }` |
| `POST` | `/logout` | Cerrar sesión | — |
| `GET` | `/me` | Datos del usuario en sesión | — |

### Administración (`admin_required`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/admin/usuarios` | Listar todos los usuarios registrados |

### Portafolios (`login_required`)

| Método | Endpoint | Descripción | Body |
|--------|----------|-------------|------|
| `GET` | `/portafolios` | Listar portafolios del usuario | — |
| `POST` | `/portafolios` | Crear nuevo portafolio | `{ nombre, descripcion, moneda_base }` |
| `DELETE` | `/portafolios/<id>` | Eliminar portafolio | — |

### Activos

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `GET` | `/activos` | `login_required` | Listar activos (filtro opcional `?tipo=accion`) |
| `POST` | `/activos` | `admin_required` | Crear nuevo activo en el catálogo |

### Transacciones (`login_required`)

| Método | Endpoint | Descripción | Body |
|--------|----------|-------------|------|
| `GET` | `/transacciones?portafolio_id=X` | Listar transacciones del portafolio | — |
| `POST` | `/transacciones` | Registrar transacción | `{ portafolio_id, activo_id, tipo, cantidad, precio_unitario, comision, fecha }` |
| `DELETE` | `/transacciones/<id>` | Eliminar transacción | — |

Tipos de transacción: `compra`, `venta`, `dividendo`

### Resumen y estadísticas (`login_required`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/resumen/<portafolio_id>` | Posiciones abiertas, valor de mercado, coste, P&L, distribución por tipo y sector |
| `GET` | `/estadisticas/<portafolio_id>` | Total invertido, realizado, comisiones, mayor compra |

### Precios históricos

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `GET` | `/precios?activo_id=X` | `login_required` | Últimos 365 precios de cierre |
| `POST` | `/precios` | `admin_required` | Insertar/actualizar precio (upsert) |

### Alertas (`login_required`)

| Método | Endpoint | Descripción | Body |
|--------|----------|-------------|------|
| `GET` | `/alertas` | Listar alertas del usuario | — |
| `POST` | `/alertas` | Crear alerta | `{ activo_id, tipo, valor_referencia }` |
| `DELETE` | `/alertas/<id>` | Eliminar alerta | — |

Tipos de alerta: `precio_mayor`, `precio_menor`, `variacion_porcentaje`

### Respuesta estándar de la API

```json
// Éxito
{ "status": "success", "message": "OK", "data": { ... } }

// Error
{ "status": "error", "message": "Descripción del error" }
```

---

## Pruebas

Se han implementado **tres niveles de prueba**:

### 1. Tests unitarios — `test/test_unit.py`

Verifican funciones individuales aisladas de la capa de red y base de datos:

| Test | Qué verifica |
|------|-------------|
| `test_generate_token` | El token tiene 64 caracteres hexadecimales (256 bits) |
| `test_token_unique` | Cada llamada genera un token diferente |
| `test_json_serial_datetime` | La función serializa `datetime` a ISO 8601 |
| `test_json_serial_decimal` | La función serializa `Decimal` a `float` |
| `test_json_serial_invalid` | Lanza `TypeError` con tipo no soportado |
| `test_password_hash` | bcrypt hashea y verifica correctamente |
| `test_email_validation` | Acepta emails válidos, rechaza inválidos |

```bash
pytest test/test_unit.py -v
```

### 2. Tests de integración — `test/test_integration.py`

Verifican flujos completos end-to-end usando un cliente de test de Flask:

| Test | Qué verifica |
|------|-------------|
| `test_register_success` | Registro correcto devuelve 201 |
| `test_register_duplicate_email` | Email duplicado devuelve error |
| `test_login_success` | Login correcto establece sesión y devuelve token |
| `test_login_wrong_password` | Credenciales incorrectas → 401 |
| `test_protected_without_auth` | Endpoint protegido sin sesión → 401 |
| `test_admin_endpoint_as_user` | Usuario normal en endpoint admin → 403 |
| `test_full_portfolio_flow` | Registro → Login → Crear portafolio → Listar → Eliminar |

```bash
pytest test/test_integration.py -v
```

### 3. Pruebas manuales — Colección Postman

El fichero `Portafolio-Pro.postman_collection.json` incluye una colección completa importable en Postman con:

- `01 - Registrar usuario` — POST `/api/register`
- `02 - Login` — POST `/api/login` + guarda variables de entorno
- `03 - Obtener usuario actual` — GET `/api/me`
- `04 - Listar portafolios` — GET `/api/portafolios`

Cada request incluye **scripts de test automáticos** que verifican:
- Código de respuesta HTTP correcto
- `status: 'success'` en el body
- Presencia de campos requeridos en la respuesta

### Ejecutar todos los tests

```bash
# Todos los tests
pytest test/ -v

# Con informe de cobertura
pytest test/ -v --cov=app --cov-report=term-missing

# Solo unitarios
pytest test/test_unit.py -v

# Solo integración
pytest test/test_integration.py -v
```

---

##  CI/CD con GitHub Actions

Fichero: `.github/workflows/ci.yml`

El pipeline se ejecuta automáticamente en cada `push` y `pull request` a cualquier rama.

### Pasos del pipeline

```
1. Checkout del código
2. Configurar Python 3.12
3. Instalar dependencias (pip install -r requirements.txt)
4. Ejecutar tests unitarios (pytest test/test_unit.py -v)
5. Ejecutar tests de integración (pytest test/test_integration.py -v)
```

Esto garantiza que **ningún código que rompa los tests pueda llegar a `main`** sin ser detectado.

---

##  Gestión de versiones con Git

El proyecto sigue un flujo **GitFlow simplificado**, con ramas de características que se fusionan a `main` mediante Pull Request.

### Ramas del proyecto

| Rama | Descripción | Estado |
|------|------------|--------|
| `main` | Rama principal estable y desplegable | ✅ Activa |
| `feature/roles-admin` | Autenticación, roles `user`/`admin`, decoradores de seguridad | ✅ Fusionada |
| `feature/docker` | Dockerfile, docker-compose.yml, configuración de contenedores | ✅ Fusionada |
| `feature/tests` | Tests unitarios, tests de integración, configuración pytest | ✅ Fusionada |
| `feature/ci-actions` | Pipeline GitHub Actions (`.github/workflows/ci.yml`) | ✅ Fusionada |
| `feature/docs` | README.md, OWASP.md, documentación del proyecto | ✅ Fusionada |

### Flujo de trabajo seguido

```
main
 ├── feature/roles-admin  →  (PR)  →  main
 ├── feature/docker       →  (PR)  →  main
 ├── feature/tests        →  (PR)  →  main
 ├── feature/ci-actions   →  (PR)  →  main
 └── feature/docs         →  (PR)  →  main
```

He tenido un problema con las ramas y sin querer he ido subiendolo todo a la rama main pero estan las ramas necesarias creadas:


---

##  Seguridad aplicada — OWASP

Ver análisis detallado en [`OWASP.md`](OWASP.md).

### Resumen de medidas implementadas

| OWASP | Riesgo                                   | Medida en el código                                                      |
| ----- | ---------------------------------------- | ------------------------------------------------------------------------ |
| A01   | Control de acceso roto                   | @login_required / @admin_required + filtro por session['user_id']        |
| A02   | Fallos criptográficos                    | bcrypt + secrets.token_hex(32) + variables de entorno                    |
| A03   | Inyección                                | SQL parametrizado con %s en todas las consultas                          |
| A04   | Diseño inseguro                          | Modelo de roles, tokens por usuario, separación frontend/backend         |
| A05   | Configuración de seguridad incorrecta    | Flask-Talisman (CSP, HSTS) + Flask-CORS restringido                      |
| A07   | Fallos de identificación y autenticación | Login seguro, session.clear() en logout, cookies HttpOnly + SameSite=Lax |

```python
# Cookies de sesión seguras (app.py)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,    # No accesible desde JavaScript → XSS mitigado
    SESSION_COOKIE_SAMESITE='Lax',   # Mitiga ataques CSRF
    SESSION_COOKIE_SECURE=False,     # → True en producción con HTTPS
)
```
