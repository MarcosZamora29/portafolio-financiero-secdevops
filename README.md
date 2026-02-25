# =====================================================
# PORTAFOLIO FINANCIERO — GUÍA DE INSTALACIÓN
# =====================================================

## ESTRUCTURA DEL PROYECTO
```
portafolio-financiero/
├── index.html          ← Frontend (abrir en VS Code con Live Server)
├── app.py              ← Backend Python (Flask)
├── requirements.txt    ← Dependencias Python
└── portfolio_db.sql    ← Script SQL para phpMyAdmin
```

---

## PASO 1 — BASE DE DATOS (phpMyAdmin)
1. Abre phpMyAdmin: http://localhost/phpmyadmin
2. Haz clic en "Importar"
3. Selecciona el archivo `portfolio_db.sql`
4. Haz clic en "Continuar"
✅ La BD "portafolio_financiero" quedará creada con datos de ejemplo.

---

## PASO 2 — BACKEND PYTHON

### Instalar dependencias:
```bash
pip install flask flask-cors mysql-connector-python bcrypt
```

### Configurar BD (en app.py, líneas ~30-37):
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",      # ← Tu usuario MySQL
    "password": "",          # ← Tu contraseña MySQL
    "database": "portafolio_financiero",
    "port":     3306
}
```

### Ejecutar:
```bash
python app.py
```
Backend disponible en: http://localhost:5000

---

## PASO 3 — FRONTEND

### Opción A — VS Code Live Server (recomendado):
1. Instala la extensión "Live Server" en VS Code
2. Click derecho en `index.html` → "Open with Live Server"
3. Se abre en http://127.0.0.1:5500

### Opción B — Abrir directamente:
- Doble clic en `index.html`

---

## USUARIO DEMO
- Email:    demo@portafolio.com
- Password: demo1234

---

## FUNCIONALIDADES
✅ Login / Registro de usuarios
✅ Múltiples portafolios por usuario
✅ Registro de transacciones (compra, venta, dividendo)
✅ Dashboard con valor de mercado y rendimiento
✅ Gráficas de distribución (por tipo y sector)
✅ Catálogo de activos (acciones, ETFs, criptos, bonos...)
✅ Alertas de precio personalizadas
✅ Precios históricos por activo

---

## API ENDPOINTS

| Método | Endpoint                    | Descripción              |
|--------|-----------------------------|--------------------------|
| POST   | /api/login                  | Iniciar sesión           |
| POST   | /api/register               | Registrar usuario        |
| POST   | /api/logout                 | Cerrar sesión            |
| GET    | /api/portafolios            | Listar portafolios       |
| POST   | /api/portafolios            | Crear portafolio         |
| DELETE | /api/portafolios/:id        | Eliminar portafolio      |
| GET    | /api/activos                | Listar activos           |
| POST   | /api/activos                | Crear activo             |
| GET    | /api/transacciones          | Listar transacciones     |
| POST   | /api/transacciones          | Crear transacción        |
| DELETE | /api/transacciones/:id      | Eliminar transacción     |
| GET    | /api/resumen/:portafolio_id | Resumen del portafolio   |
| GET    | /api/estadisticas/:id       | Estadísticas avanzadas   |
| GET    | /api/alertas                | Listar alertas           |
| POST   | /api/alertas                | Crear alerta             |
| DELETE | /api/alertas/:id            | Eliminar alerta          |
