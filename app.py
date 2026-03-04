from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_talisman import Talisman
import mysql.connector
from mysql.connector import Error
import bcrypt
import json
from datetime import datetime, date
from decimal import Decimal
import os
from functools import wraps


app = Flask(__name__)

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_change_me")

# Cookies de sesión más seguras (OWASP A05 / A07)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False  # pon True en producción con HTTPS
)

# CORS solo desde tu frontend
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "null"
])

# Cabeceras de seguridad básicas (OWASP A05)
csp = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "https://cdnjs.cloudflare.com", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
    "img-src": ["'self'", "data:"]
}

Talisman(
    app,
    content_security_policy=csp,
    force_https=False,          # True en producción con HTTPS
    session_cookie_secure=False # a juego con SESSION_COOKIE_SECURE
)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ─────────────────────────────────────────────
# CONFIGURACIÓN BASE DE DATOS (variables de entorno)
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "portafolio_financiero"),
    "port":     int(os.getenv("DB_PORT", "3306")),
}


def get_db():
    """Retorna una conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


def json_serial(obj):
    """Serializador JSON para tipos especiales."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Tipo no serializable: {type(obj)}")


def success(data=None, msg="OK", code=200):
    resp = {"status": "success", "message": msg}
    if data is not None:
        resp["data"] = data
    return app.response_class(
        response=json.dumps(resp, default=json_serial),
        status=code,
        mimetype="application/json"
    )


def error(msg="Error", code=400):
    return jsonify({"status": "error", "message": msg}), code


# ─────────────────────────────────────────────
# DECORADORES DE AUTORIZACIÓN
# ─────────────────────────────────────────────

def login_required(f):
    """Requiere que el usuario esté autenticado."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return error("No autenticado. Inicia sesión.", 401)
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Requiere que el usuario sea administrador."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return error("No autenticado. Inicia sesión.", 401)
        if session.get("user_role") != "admin":
            return error("Acceso denegado. Solo administradores.", 403)
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    d = request.json
    if not d or not all(k in d for k in ["nombre", "email", "password"]):
        return error("Campos requeridos: nombre, email, password")

    # Validación mínima
    if len(d["password"]) < 8:
        return error("La contraseña debe tener al menos 8 caracteres")
    if "@" not in d["email"]:
        return error("Email inválido")

    pw_hash = bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode()

    conn = get_db()
    if not conn:
        return error("Error de conexión a BD", 500)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s, %s, %s, %s)",
            (d["nombre"], d["email"], pw_hash, "user")  # rol por defecto: user
        )
        conn.commit()
        uid = cur.lastrowid
        cur.execute(
            "INSERT INTO portafolios (usuario_id, nombre, descripcion) VALUES (%s, %s, %s)",
            (uid, "Mi Portafolio", "Portafolio principal")
        )
        conn.commit()
        return success({"usuario_id": uid}, "Usuario registrado correctamente", 201)
    except Error as e:
        if "Duplicate entry" in str(e):
            return error("El email ya está registrado")
        return error(str(e), 500)
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    d = request.json
    if not d or not all(k in d for k in ["email", "password"]):
        return error("Email y contraseña requeridos")

    conn = get_db()
    if not conn:
        return error("Error de conexión a BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE email=%s AND activo=1", (d["email"],))
        user = cur.fetchone()

        # Mensaje genérico
        if not user or not bcrypt.checkpw(d["password"].encode(), user["password_hash"].encode()):
            return error("Credenciales incorrectas", 401)

        session["user_id"]   = user["id"]
        session["user_name"] = user["nombre"]
        session["user_role"] = user.get("rol", "user")

        return success({
            "id":     user["id"],
            "nombre": user["nombre"],
            "email":  user["email"],
            "rol":    user.get("rol", "user")
        }, "Login exitoso")
    finally:
        conn.close()


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return success(msg="Sesión cerrada")


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return success({
        "id":     session["user_id"],
        "nombre": session["user_name"],
        "rol":    session.get("user_role", "user")
    })


# ─────────────────────────────────────────────
# ADMIN - Endpoint exclusivo administrador
# ─────────────────────────────────────────────

@app.route("/api/admin/usuarios", methods=["GET"])
@admin_required
def listar_usuarios():
    """Solo el admin puede ver todos los usuarios registrados."""
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, email, rol, activo FROM usuarios ORDER BY id")
        return success(cur.fetchall())
    finally:
        conn.close()


# ─────────────────────────────────────────────
# PORTAFOLIOS
# ─────────────────────────────────────────────

@app.route("/api/portafolios", methods=["GET"])
@login_required
def listar_portafolios():
    uid = session.get("user_id")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM portafolios WHERE usuario_id=%s", (uid,))
        return success(cur.fetchall())
    finally:
        conn.close()


@app.route("/api/portafolios", methods=["POST"])
@login_required
def crear_portafolio():
    d = request.json
    uid = session.get("user_id")
    if not d or not d.get("nombre"):
        return error("nombre requerido")

    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO portafolios (usuario_id, nombre, descripcion, moneda_base) VALUES (%s,%s,%s,%s)",
            (uid, d["nombre"], d.get("descripcion", ""), d.get("moneda_base", "USD"))
        )
        conn.commit()
        return success({"id": cur.lastrowid}, "Portafolio creado", 201)
    finally:
        conn.close()


@app.route("/api/portafolios/<int:pid>", methods=["DELETE"])
@login_required
def eliminar_portafolio(pid):
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM portafolios WHERE id=%s", (pid,))
        conn.commit()
        return success(msg="Portafolio eliminado")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ACTIVOS
# ─────────────────────────────────────────────

@app.route("/api/activos", methods=["GET"])
@login_required
def listar_activos():
    tipo = request.args.get("tipo")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        if tipo:
            cur.execute("SELECT * FROM activos WHERE tipo=%s ORDER BY ticker", (tipo,))
        else:
            cur.execute("SELECT * FROM activos ORDER BY ticker")
        return success(cur.fetchall())
    finally:
        conn.close()


@app.route("/api/activos", methods=["POST"])
@admin_required  # Solo admin puede crear activos
def crear_activo():
    d = request.json
    if not d or not all(k in d for k in ["ticker", "nombre", "tipo"]):
        return error("ticker, nombre y tipo son requeridos")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activos (ticker, nombre, tipo, sector, moneda, descripcion) VALUES (%s,%s,%s,%s,%s,%s)",
            (d["ticker"].upper(), d["nombre"], d["tipo"],
             d.get("sector", ""), d.get("moneda", "USD"), d.get("descripcion", ""))
        )
        conn.commit()
        return success({"id": cur.lastrowid}, "Activo creado", 201)
    except Error as e:
        if "Duplicate" in str(e):
            return error("El ticker ya existe")
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# TRANSACCIONES
# ─────────────────────────────────────────────

@app.route("/api/transacciones", methods=["GET"])
@login_required
def listar_transacciones():
    pid = request.args.get("portafolio_id")
    if not pid:
        return error("portafolio_id requerido")

    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT t.*, a.ticker, a.nombre as activo_nombre, a.tipo as activo_tipo
            FROM transacciones t
            JOIN activos a ON a.id = t.activo_id
            WHERE t.portafolio_id = %s
            ORDER BY t.fecha DESC
        """, (pid,))
        return success(cur.fetchall())
    finally:
        conn.close()


@app.route("/api/transacciones", methods=["POST"])
@login_required
def crear_transaccion():
    d = request.json
    if not d or not all(k in d for k in ["portafolio_id", "activo_id", "tipo", "cantidad", "precio_unitario", "fecha"]):
        return error("Faltan campos requeridos")

    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transacciones
              (portafolio_id, activo_id, tipo, cantidad, precio_unitario, comision, fecha, notas)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            d["portafolio_id"], d["activo_id"], d["tipo"],
            d["cantidad"], d["precio_unitario"],
            d.get("comision", 0), d["fecha"], d.get("notas", "")
        ))
        conn.commit()
        return success({"id": cur.lastrowid}, "Transacción registrada", 201)
    finally:
        conn.close()


@app.route("/api/transacciones/<int:tid>", methods=["DELETE"])
@login_required
def eliminar_transaccion(tid):
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM transacciones WHERE id=%s", (tid,))
        conn.commit()
        return success(msg="Transacción eliminada")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# RESUMEN / DASHBOARD
# ─────────────────────────────────────────────

@app.route("/api/resumen/<int:pid>", methods=["GET"])
@login_required
def resumen_portafolio(pid):
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
                a.id, a.ticker, a.nombre, a.tipo, a.sector, a.moneda,
                SUM(CASE WHEN t.tipo='compra'    THEN t.cantidad  ELSE 0 END) as cant_comprada,
                SUM(CASE WHEN t.tipo='venta'     THEN t.cantidad  ELSE 0 END) as cant_vendida,
                SUM(CASE WHEN t.tipo='compra'    THEN t.cantidad*t.precio_unitario+t.comision ELSE 0 END) as costo_total,
                SUM(CASE WHEN t.tipo='venta'     THEN t.cantidad*t.precio_unitario-t.comision ELSE 0 END) as ingreso_ventas,
                SUM(CASE WHEN t.tipo='dividendo' THEN t.cantidad*t.precio_unitario ELSE 0 END) as dividendos,
                COUNT(t.id) as num_transacciones
            FROM transacciones t
            JOIN activos a ON a.id = t.activo_id
            WHERE t.portafolio_id = %s
            GROUP BY a.id, a.ticker, a.nombre, a.tipo, a.sector, a.moneda
            HAVING (cant_comprada - cant_vendida) > 0
        """, (pid,))
        posiciones_raw = cur.fetchall()

        posiciones = []
        costo_total_portafolio = 0

        for p in posiciones_raw:
            cantidad_neta = float(p["cant_comprada"]) - float(p["cant_vendida"])
            costo_total   = float(p["costo_total"])
            costo_neto    = costo_total - float(p["ingreso_ventas"])
            precio_prom   = costo_neto / cantidad_neta if cantidad_neta > 0 else 0

            cur.execute("""
                SELECT precio_cierre FROM precios_historicos
                WHERE activo_id=%s ORDER BY fecha DESC LIMIT 1
            """, (p["id"],))
            prec_row = cur.fetchone()
            precio_actual = float(prec_row["precio_cierre"]) if prec_row else precio_prom

            valor_mercado   = cantidad_neta * precio_actual
            ganancia_neta   = valor_mercado - costo_neto + float(p["dividendos"])
            rendimiento_pct = (ganancia_neta / costo_neto * 100) if costo_neto > 0 else 0

            costo_total_portafolio += costo_neto

            posiciones.append({
                "activo_id":       p["id"],
                "ticker":          p["ticker"],
                "nombre":          p["nombre"],
                "tipo":            p["tipo"],
                "sector":          p["sector"],
                "cantidad":        round(cantidad_neta, 6),
                "precio_promedio": round(precio_prom, 4),
                "precio_actual":   round(precio_actual, 4),
                "costo_total":     round(costo_neto, 2),
                "valor_mercado":   round(valor_mercado, 2),
                "ganancia_neta":   round(ganancia_neta, 2),
                "rendimiento_pct": round(rendimiento_pct, 2),
                "dividendos":      round(float(p["dividendos"]), 2),
            })

        valor_total    = sum(p["valor_mercado"] for p in posiciones)
        ganancia_total = sum(p["ganancia_neta"] for p in posiciones)
        rend_total     = (ganancia_total / costo_total_portafolio * 100) if costo_total_portafolio > 0 else 0

        dist_tipo = {}
        for p in posiciones:
            dist_tipo[p["tipo"]] = dist_tipo.get(p["tipo"], 0) + p["valor_mercado"]

        dist_sector = {}
        for p in posiciones:
            s = p["sector"] or "Otro"
            dist_sector[s] = dist_sector.get(s, 0) + p["valor_mercado"]

        return success({
            "posiciones":      posiciones,
            "valor_total":     round(valor_total, 2),
            "costo_total":     round(costo_total_portafolio, 2),
            "ganancia_total":  round(ganancia_total, 2),
            "rendimiento_pct": round(rend_total, 2),
            "dist_tipo":       dist_tipo,
            "dist_sector":     dist_sector,
        })
    finally:
        conn.close()


# ─────────────────────────────────────────────
# PRECIOS HISTÓRICOS
# ─────────────────────────────────────────────

@app.route("/api/precios", methods=["GET"])
@login_required
def listar_precios():
    activo_id = request.args.get("activo_id")
    if not activo_id:
        return error("activo_id requerido")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT fecha, precio_cierre, volumen FROM precios_historicos
            WHERE activo_id=%s ORDER BY fecha ASC LIMIT 365
        """, (activo_id,))
        return success(cur.fetchall())
    finally:
        conn.close()


@app.route("/api/precios", methods=["POST"])
@admin_required  # Solo admin puede cargar precios históricos
def agregar_precio():
    d = request.json
    if not d or not all(k in d for k in ["activo_id", "fecha", "precio_cierre"]):
        return error("activo_id, fecha y precio_cierre requeridos")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO precios_historicos (activo_id, fecha, precio_cierre, volumen)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE precio_cierre=VALUES(precio_cierre), volumen=VALUES(volumen)
        """, (d["activo_id"], d["fecha"], d["precio_cierre"], d.get("volumen")))
        conn.commit()
        return success(msg="Precio registrado")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ALERTAS
# ─────────────────────────────────────────────

@app.route("/api/alertas", methods=["GET"])
@login_required
def listar_alertas():
    uid = session.get("user_id")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT al.*, a.ticker, a.nombre as activo_nombre
            FROM alertas al JOIN activos a ON a.id=al.activo_id
            WHERE al.usuario_id=%s ORDER BY al.fecha_creacion DESC
        """, (uid,))
        return success(cur.fetchall())
    finally:
        conn.close()


@app.route("/api/alertas", methods=["POST"])
@login_required
def crear_alerta():
    d = request.json
    uid = session.get("user_id")
    if not d or not all(k in d for k in ["activo_id", "tipo", "valor_referencia"]):
        return error("Faltan campos requeridos")
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO alertas (usuario_id, activo_id, tipo, valor_referencia)
            VALUES (%s,%s,%s,%s)
        """, (uid, d["activo_id"], d["tipo"], d["valor_referencia"]))
        conn.commit()
        return success({"id": cur.lastrowid}, "Alerta creada", 201)
    finally:
        conn.close()


@app.route("/api/alertas/<int:aid>", methods=["DELETE"])
@login_required
def eliminar_alerta(aid):
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM alertas WHERE id=%s", (aid,))
        conn.commit()
        return success(msg="Alerta eliminada")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ESTADÍSTICAS AVANZADAS
# ─────────────────────────────────────────────

@app.route("/api/estadisticas/<int:pid>", methods=["GET"])
@login_required
def estadisticas(pid):
    conn = get_db()
    if not conn:
        return error("Error BD", 500)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
                SUM(CASE WHEN tipo='compra' THEN cantidad*precio_unitario+comision ELSE 0 END) as total_invertido,
                SUM(CASE WHEN tipo='venta'  THEN cantidad*precio_unitario-comision ELSE 0 END) as total_realizado,
                SUM(comision) as total_comisiones,
                COUNT(*) as total_transacciones
            FROM transacciones WHERE portafolio_id=%s
        """, (pid,))
        stats = cur.fetchone()

        cur.execute("""
            SELECT t.*, a.ticker,
                   (t.precio_unitario * t.cantidad) as valor
            FROM transacciones t JOIN activos a ON a.id=t.activo_id
            WHERE t.portafolio_id=%s AND t.tipo='compra'
            ORDER BY valor DESC LIMIT 1
        """, (pid,))
        mayor_compra = cur.fetchone()

        return success({
            "total_invertido":     float(stats["total_invertido"] or 0),
            "total_realizado":     float(stats["total_realizado"] or 0),
            "total_comisiones":    float(stats["total_comisiones"] or 0),
            "total_transacciones": stats["total_transacciones"],
            "mayor_compra":        mayor_compra
        })
    finally:
        conn.close()


# ─────────────────────────────────────────────
# INICIO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print("=" * 55)
    print("  PORTAFOLIO FINANCIERO - BACKEND FLASK")
    print(f"  Modo debug: {debug_mode}")
    print("  Servidor: http://localhost:5000")
    print("=" * 55)
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
