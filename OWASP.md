# Análisis OWASP Top 10

Este documento describe cómo se han tenido en cuenta los riesgos de seguridad
del OWASP Top 10 (Web y API) en el desarrollo de la aplicación
**Portafolio Financiero**.

---

## Resumen rápido

| Riesgo OWASP              | Estado              | Comentario breve                         |
|---------------------------|---------------------|------------------------------------------|
| A01 Broken Access Control | Mitigado parcialmente | Control por sesión y rol, falta RLS BD  |
| A02 Crypto Failures       | Mitigado             | Bcrypt, secretos por entorno             |
| A03 Injection             | Mitigado             | SQL parametrizado                        |
| A04 Insecure Design       | Parcial              | Roles, tokens; falta rate limiting       |
| A05 Security Misconfig    | Parcial              | Talisman, CORS; falta hardening prod     |
| A06 Vulnerable Components | Pendiente            | Falta proceso formal de actualización    |
| A07 Auth & Identification | Mitigado             | Login seguro, sesiones y cookies         |
| A08 Software Integrity    | Pendiente            | No hay firmas/CI con controles todavía   |
| A09 Security Logging      | Parcial              | Logs básicos, falta SIEM/alertas         |
| A10 SSRF / Otros          | Bajo impacto         | No se llaman URLs externas desde usuario |

---

## OWASP Top 10 - Aplicaciones Web

### A01 - Broken Access Control
**Riesgo:** Usuarios acceden a recursos que no les pertenecen.

**Medidas aplicadas:**
- Todos los endpoints de la API que manejan datos de usuario están protegidos con el decorador `@login_required`, que verifica la sesión activa antes de procesar cualquier petición.
- Los endpoints exclusivos de administración (`/api/admin/usuarios`, creación de activos, carga de precios, etc.) están protegidos con `@admin_required`, que además verifica que el rol del usuario en sesión sea `admin`.
- Los datos de portafolios y alertas se filtran siempre por `usuario_id` extraído de la sesión del servidor, nunca por un valor enviado por el cliente.
- No se exponen endpoints públicos que permitan modificar datos sin autenticación.


---

### A02 - Cryptographic Failures
**Riesgo:** Exposición de datos sensibles por cifrado débil o inexistente.

**Medidas aplicadas:**
- Las contraseñas se almacenan usando **bcrypt** con salt aleatorio, nunca en texto plano ni con algoritmos débiles (MD5/SHA1).
- La `SECRET_KEY` de Flask y las credenciales de base de datos se gestionan mediante **variables de entorno** (`.env` / entorno Docker), nunca hardcodeadas en el código fuente.
- El fichero `.env` está incluido en `.gitignore` para que no se suba al repositorio.
- Los tokens de API se generan con `secrets.token_hex(32)`, proporcionando alta entropía criptográfica.

---

### A03 - Injection
**Riesgo:** Inyección SQL, comandos o código malicioso.

**Medidas aplicadas:**
- Todas las consultas SQL utilizan **parámetros preparados** (`%s`), nunca concatenación de strings con datos del usuario.
- Ejemplo seguro usado en el código:
  ```python
  cur.execute("SELECT * FROM usuarios WHERE email=%s AND activo=1", (email,))

**A04 - Insecure Design:**

Riesgo: Ausencia de controles de seguridad en el propio diseño de la aplicación.

Medidas aplicadas:

Modelo de roles sencillo (user / admin) para separar capacidades.

Diseño de endpoints que siempre operan sobre recursos ligados al usuario en sesión.

Generación de tokens de API por usuario, pensados para uso futuro desde integraciones externas.


**A05 - Vulnerable and Outdated Components**

Situación actual:

Las dependencias se gestionan con requirements.txt.

No hay aún un proceso formal de escaneo de vulnerabilidades en imágenes Docker o paquetes Python.


**A06 - Identification and Authentication Failures**

Riesgo: Fallos en mecanismos de login, logout, gestión de sesiones y tokens.

Medidas aplicadas:

Proceso de login robusto:

Verificación de credenciales con bcrypt.

Mensajes de error genéricos para no filtrar si el email existe o no.

Gestión correcta de sesión:

En login se establecen los datos en session.

En logout se hace session.clear() para invalidar la sesión.

Decoradores que aseguran autenticación antes de acceder a recursos protegidos.

Token de API generado en cada login y almacenado en BD, único por usuario y con alta entropía.


**A07 - Software and Data Integrity Failures**

Riesgo: Integridad de código y datos comprometida (supply chain, actualizaciones maliciosas, etc.).

Situación actual:

No se han implementado aún mecanismos específicos de validación de integridad de artefactos (firmas, checksum).

Despliegues gestionados manualmente / con Docker Compose.

Mejoras futuras:

Introducir un pipeline CI/CD con:

Build reproducibles.

Firmado de imágenes Docker.

Versionar y revisar los scripts SQL y migraciones.

**A08 - Security Logging and Monitoring Failures**

Riesgo: Falta de logs y monitorización que impiden detectar ataques.

Situación actual:

Logs básicos en consola:

Errores de conexión a BD con prefijo [DB ERROR].

Flask registra errores estándar en consola / logs del contenedor.


