# Análisis OWASP Top 10

Este documento describe cómo se han tenido en cuenta los riesgos de seguridad
del OWASP Top 10 (Web y API) en el desarrollo de la aplicación
**Portafolio Financiero**.

---

## OWASP Top 10 - Aplicaciones Web

### A01 - Broken Access Control
**Riesgo:** Usuarios acceden a recursos que no les pertenecen.

**Medidas aplicadas:**
- Todos los endpoints de la API están protegidos con el decorador
  `@login_required`, que verifica la sesión activa antes de procesar
  cualquier petición.
- Los endpoints exclusivos de administración (`/api/admin/usuarios`,
  creación de activos, carga de precios) están protegidos con
  `@admin_required`, que además verifica que el rol sea `admin`.
- Los datos de portafolios se filtran siempre por `usuario_id` extraído
  de la sesión del servidor, nunca del cliente.

---

### A02 - Cryptographic Failures
**Riesgo:** Exposición de datos sensibles por cifrado débil o inexistente.

**Medidas aplicadas:**
- Las contraseñas se almacenan usando **bcrypt** con salt aleatorio,
  nunca en texto plano ni con MD5/SHA1.
- La `SECRET_KEY` de Flask y las credenciales de base de datos se
  gestionan exclusivamente mediante **variables de entorno** (fichero
  `.env`), nunca hardcodeadas en el código fuente.
- El fichero `.env` está incluido en `.gitignore` para que nunca
  se suba al repositorio.

---

### A03 - Injection
**Riesgo:** Inyección SQL, comandos o código malicioso.

**Medidas aplicadas:**
- Todas las consultas SQL utilizan **parámetros preparados** (`%s`),
  nunca concatenación de strings con datos del usuario.
- Ejemplo seguro usado en el código:
  ```python
  cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
