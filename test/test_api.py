import pytest


class TestPortafoliosAuth:
    """Tests de integración: endpoints protegidos sin sesión"""

    def test_listar_portafolios_sin_auth(self, client):
        """Sin login debe devolver 401"""
        res = client.get("/api/portafolios")
        assert res.status_code == 401

    def test_crear_portafolio_sin_auth(self, client):
        """Sin login debe devolver 401"""
        res = client.post("/api/portafolios", json={"nombre": "Test"})
        assert res.status_code == 401


class TestActivosAuth:
    """Tests de integración: activos protegidos"""

    def test_listar_activos_sin_auth(self, client):
        """Sin login debe devolver 401"""
        res = client.get("/api/activos")
        assert res.status_code == 401

    def test_crear_activo_sin_auth(self, client):
        """Crear activo sin login debe devolver 401"""
        res = client.post("/api/activos", json={
            "ticker": "AAPL",
            "nombre": "Apple",
            "tipo": "accion"
        })
        assert res.status_code == 401


class TestAdminAuth:
    """Tests de integración: endpoints exclusivos de admin"""

    def test_admin_usuarios_sin_auth(self, client):
        """Sin login debe devolver 401"""
        res = client.get("/api/admin/usuarios")
        assert res.status_code == 401

    def test_admin_usuarios_con_user_normal(self, client):
        """Usuario normal debe recibir 403"""
        with client.session_transaction() as sess:
            sess["user_id"] = 999
            sess["user_name"] = "Usuario Normal"
            sess["user_role"] = "user"  # rol user, no admin

        res = client.get("/api/admin/usuarios")
        assert res.status_code == 403
        data = res.get_json()
        assert data["status"] == "error"

    def test_admin_crear_activo_con_user_normal(self, client):
        """Usuario normal no puede crear activos, debe recibir 403"""
        with client.session_transaction() as sess:
            sess["user_id"] = 999
            sess["user_name"] = "Usuario Normal"
            sess["user_role"] = "user"

        res = client.post("/api/activos", json={
            "ticker": "TSLA",
            "nombre": "Tesla",
            "tipo": "accion"
        })
        assert res.status_code == 403


class TestTransaccionesAuth:
    """Tests de integración: transacciones protegidas"""

    def test_listar_transacciones_sin_auth(self, client):
        res = client.get("/api/transacciones?portafolio_id=1")
        assert res.status_code == 401

    def test_crear_transaccion_sin_auth(self, client):
        res = client.post("/api/transacciones", json={})
        assert res.status_code == 401
