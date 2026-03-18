# 🛡️ Análisis de Seguridad — OWASP Top 10

Este documento describe cómo se han tenido en cuenta los riesgos del **OWASP Top 10** (Aplicaciones Web y APIs) en el desarrollo de **Portafolio Pro**.

---

##  Resumen ejecutivo

| # | Riesgo OWASP | Estado | Medida principal |
|---|-------------|--------|-----------------|
| A01 | Broken Access Control | Mitigado | Decoradores `@login_required` / `@admin_required` |
| A02 | Cryptographic Failures | Mitigado | bcrypt + secrets + variables de entorno |
| A03 | Injection | Mitigado | SQL parametrizado en todas las consultas |
| A04 | Insecure Design | Parcial | Roles, tokens — falta rate limiting |
| A05 | Security Misconfiguration | Parcial | Talisman + CORS — falta hardening en producción |
| A06 | Vulnerable Components | Mitigado | requirements.txt — escaneo automático |
| A07 | Auth & Identification Failures | Mitigado | Login seguro, sesiones, cookies HttpOnly/SameSite |
| A08 | Software & Data Integrity | Parcial | CI/CD con GitHub Actions — falta firmado de imágenes |
| A09 | Security Logging & Monitoring |  Parcial | Logs básicos — falta SIEM |
| A10 | SSRF | ✅N/A | No se realizan peticiones a URLs externas desde el usuario |

---

## OWASP Top 10 — Aplicaciones Web

---

### A01 — Broken Access Control
**Riesgo:** Usuarios acceden a recursos o funciones que no les corresponden.

**Medidas aplicadas:**
- Todos los endpoints de la API están protegidos con el decorador `@login_required`, que verifica la existencia de `session['user_id']` antes de procesar cualquier petición.
- Los endpoints exclusivos de administración (`GET /api/admin/usuarios`, `POST /api/activos`, `POST /api/precios`) están protegidos con `@admin_required`, que además verifica que `session['user_role'] == 'admin'`.
- Los datos de portafolios y alertas se filtran **siempre por `usuario_id` extraído de la sesión del servidor**, nunca por valores enviados por el cliente, evitando el patrón IDOR (Insecure Direct Object Reference).
- No existen endpoints públicos que permitan modificar o leer datos sin autenticación previa.

```python
# Ejemplo en app.py
@app.route('/api/portafolios', methods=['GET'])
@login_required
def listar_portafolios():
    uid = session.get('user_id')   # ← siempre de la sesión, nunca del body
    cur.execute("SELECT * FROM portafolios WHERE usuario_id = %s", (uid,))
```

**Pendiente de mejorar:**
- Implementar Row-Level Security (RLS) a nivel de base de datos como capa adicional.
- Añadir comprobación de ownership en las operaciones DELETE de transacciones y alertas.

---

### A02 — Cryptographic Failures
**Riesgo:** Exposición de datos sensibles por cifrado débil o inexistente.

**Medidas aplicadas:**
- Las contraseñas se almacenan usando **bcrypt con salt aleatorio** generado por `bcrypt.gensalt()`. Nunca se almacenan en texto plano ni con algoritmos débiles (MD5, SHA1).
- La `SECRET_KEY` de Flask y las credenciales de base de datos se gestionan mediante **variables de entorno** (`.env` + Docker environment), nunca hardcodeadas en el código fuente.
- El fichero `.env` está incluido en `.gitignore` para que no se suba accidentalmente al repositorio.
- Los tokens de API se generan con `secrets.token_hex(32)`, proporcionando **256 bits de entropía criptográfica**.

```python
# Hash seguro de contraseña
pw_hash = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt()).decode()

# Verificación segura
bcrypt.checkpw(d['password'].encode(), user['password_hash'].encode())

# Token de alta entropía
token = secrets.token_hex(32)  # 64 caracteres hex = 256 bits
```

---

### A03 — Injection
**Riesgo:** Inyección SQL, comandos o código malicioso a través de inputs del usuario.

**Medidas aplicadas:**
- **Todas** las consultas SQL utilizan **parámetros preparados** (`%s`), sin concatenación de strings con datos del usuario.
- No se ejecutan comandos del sistema operativo con datos controlados por el usuario.
- No se usa `eval()` ni `exec()` en ninguna parte del código.

```python
# Correcto — parametrizado
cur.execute("SELECT * FROM usuarios WHERE email = %s AND activo = 1", (email,))

# Incorrecto — nunca se hace esto
cur.execute(f"SELECT * FROM usuarios WHERE email = '{email}'")
```

---

### A04 — Insecure Design
**Riesgo:** Ausencia de controles de seguridad en el propio diseño de la aplicación.

**Medidas aplicadas:**
- Modelo de roles (`user` / `admin`) separando capacidades desde el diseño.
- Todos los endpoints operan sobre recursos ligados al usuario en sesión.
- Tokens de API únicos por usuario con alta entropía, renovados en cada login.
- Separación clara entre frontend (HTML estático) y backend (API REST).

**Pendiente de mejorar:**
- Implementar **rate limiting** en los endpoints de autenticación (`/api/login`, `/api/register`) para prevenir ataques de fuerza bruta (usando `Flask-Limiter`).
- Añadir bloqueo temporal de cuenta tras N intentos fallidos.

---

### A05 — Security Misconfiguration
**Riesgo:** Configuración insegura de componentes, cabeceras HTTP o servicios.

**Medidas aplicadas:**
- **Flask-Talisman** configura automáticamente cabeceras de seguridad HTTP:
  - `Content-Security-Policy (CSP)` — Restringe orígenes de scripts, estilos, imágenes y fuentes
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `Strict-Transport-Security` (activo en producción con HTTPS)
- **Flask-CORS** permite únicamente los orígenes `http://localhost:5000`, `http://127.0.0.1:5000` y `null` (desarrollo local).
- Las credenciales de base de datos se pasan por variables de entorno en `docker-compose.yml`, no en el código.
- `FLASK_DEBUG=false` en producción.

```python
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "https://cdnjs.cloudflare.com", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "data:"],
    'img-src': ["'self'", "data:"]
}
Talisman(app, content_security_policy=csp, force_https=False)
```

**Pendiente de mejorar:**
- En producción: activar `force_https=True` y `SESSION_COOKIE_SECURE=True`.
- Eliminar `'unsafe-inline'` del CSP sustituyendo por nonces.

---

### A06 — Vulnerable and Outdated Components
**Riesgo:** Uso de componentes con vulnerabilidades conocidas.

**Situación actual:**
- Las dependencias se gestionan con `requirements.txt` con versiones fijadas.
- El pipeline de GitHub Actions ejecuta `pip install` con las versiones declaradas.

**Pendiente de mejorar:**
- Integrar **`pip audit`** o **Dependabot** en el pipeline CI para escanear vulnerabilidades automáticamente.
- Escanear la imagen Docker con **Trivy** o **Snyk**.

---

### A07 — Identification and Authentication Failures
**Riesgo:** Fallos en mecanismos de login, logout, gestión de sesiones y tokens.

**Medidas aplicadas:**
- Verificación de credenciales con **bcrypt** (tiempo constante, resistente a timing attacks).
- **Mensajes de error genéricos** — no se revela si el email existe o no en el sistema.
- En login se establecen correctamente los datos en `session` del servidor.
- En logout se ejecuta `session.clear()` para invalidar completamente la sesión.
- Cookies de sesión configuradas de forma segura:

```python
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # No accesible desde JavaScript
    SESSION_COOKIE_SAMESITE='Lax',  # Mitiga ataques CSRF
    SESSION_COOKIE_SECURE=False,    # → True en producción con HTTPS
)
```

- Token de API generado en cada login con `secrets.token_hex(32)`, único por usuario y almacenado en BD.

---

### A08 — Software and Data Integrity Failures
**Riesgo:** Código o datos comprometidos por falta de verificación de integridad.

**Medidas aplicadas:**
- Pipeline **GitHub Actions** que ejecuta tests automáticamente en cada push, asegurando que solo código que pasa los tests llega a `main`.
- Fichero `requirements.txt` con versiones fijadas para builds reproducibles.
- Scripts SQL versionados en el repositorio (`portfolio_db.sql`).

**Pendiente de mejorar:**
- Firmado de imágenes Docker con Docker Content Trust.
- Verificación de checksums de dependencias con `pip hash`.

---

### A09 — Security Logging and Monitoring Failures
**Riesgo:** Falta de logs y monitorización que impiden detectar ataques.

**Situación actual:**
- Errores de conexión a BD se registran con prefijo `[DB ERROR]` en consola.
- Flask registra automáticamente errores HTTP en la consola del contenedor.
- Los logs son accesibles mediante `docker compose logs -f`.

**Pendiente de mejorar:**
- Registrar intentos de login fallidos (IP, timestamp, email).
- Implementar logging estructurado (JSON) exportable a herramientas SIEM.
- Añadir alertas ante múltiples errores 401/403 en poco tiempo.

---

### A10 — Server-Side Request Forgery (SSRF)
**Riesgo:** El servidor realiza peticiones HTTP a URLs controladas por el atacante.

**Situación:** Riesgo muy bajo / No aplicable.
- El backend no realiza ninguna petición HTTP a URLs externas basadas en input del usuario.
- No existe ningún endpoint que acepte una URL como parámetro y la consulte.
- Las únicas conexiones externas del backend son a la base de datos MySQL (host configurado por variable de entorno, no por el usuario).

---

## OWASP API Security Top 10

---

### API1 — Broken Object Level Authorization
Los recursos se filtran siempre por `usuario_id` de la sesión. Un usuario no puede acceder a los portafolios o alertas de otro aunque conozca el ID.

### API2 — Broken Authentication
Se usan sesiones seguras de Flask con cookies `HttpOnly` + `SameSite=Lax`. Los tokens de API se generan con `secrets.token_hex(32)`.

### API3 — Broken Object Property Level Authorization
Los endpoints de listado devuelven solo los campos necesarios. El endpoint `/api/admin/usuarios` excluye el `password_hash` de la respuesta.

### API4 — Unrestricted Resource Consumption
**Pendiente:** No hay rate limiting implementado actualmente. Se recomienda añadir `Flask-Limiter`.

### API5 — Broken Function Level Authorization
Las funciones de administración están separadas con `@admin_required`. Un usuario `user` que intente acceder a `/api/admin/usuarios` recibe `403 Forbidden`.

### API6 — Unrestricted Access to Sensitive Business Flows
El registro de usuarios es público pero valida longitud mínima de contraseña (8 caracteres) y formato de email. No hay límite de registros por IP actualmente.

### API7 — Server Side Request Forgery
No aplicable — el backend no realiza peticiones HTTP basadas en input del usuario.

### API8 — Security Misconfiguration
CORS configurado con orígenes explícitos. Cabeceras de seguridad gestionadas por Flask-Talisman. Variables sensibles por entorno.

### API9 — Improper Inventory Management
Todos los endpoints están documentados en el README y en la colección Postman. No existen endpoints ocultos ni versiones antiguas expuestas.

### API10 — Unsafe Consumption of APIs
El backend no consume APIs externas de terceros, por lo que este riesgo no aplica en la versión actual.

---

## Plan de mejora prioritario

1. **Alta prioridad** — Añadir `Flask-Limiter` para rate limiting en `/api/login` y `/api/register`
2. **Alta prioridad** — Activar `SESSION_COOKIE_SECURE=True` y `force_https=True` en producción
3. **Media prioridad** — Integrar `pip audit` en el pipeline CI para escaneo de dependencias
4. **Media prioridad** — Implementar logging estructurado de eventos de seguridad
5. **Baja prioridad** — Eliminar `'unsafe-inline'` del CSP sustituyendo por nonces
