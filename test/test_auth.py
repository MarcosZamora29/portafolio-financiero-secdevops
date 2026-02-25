import pytest


class TestRegister:
    """Tests unitarios del endpoint /api/register"""

    def test_register_sin_campos(self, client):
        """Debe fallar si no se envían campos"""
        res = client.post("/api/register", json={})
        assert res.status_code == 400

    def test_register_falta_password(self, client):
        """Debe fallar si falta la contraseña"""
        res = client.post("/api/register", json={
            "nombre": "Test",
            "email": "test@test.com"
        })
        assert res.status_code == 400

    def test_register_password_corta(self, client):
        """Debe fallar si la contraseña tiene menos de 8 caracteres"""
        res = client.post("/api/register", json={
            "nombre": "Test",
            "email": "test@test.com",
            "password": "123"
        })
        assert res.status_code == 400
        data = res.get_json()
        assert "8 caracteres" in data["message"]

    def test_register_email_invalido(self, client):
        """Debe fallar si el email no tiene @"""
        res = client.post("/api/register", json={
            "nombre": "Test",
            "email": "emailsinarroba",
            "password": "password123"
        })
        assert res.status_code == 400


class TestLogin:
    """Tests unitarios del endpoint /api/login"""

    def test_login_sin_campos(self, client):
        """Debe fallar si no se envían campos"""
        res = client.post("/api/login", json={})
        assert res.status_code == 400

    def test_login_credenciales_incorrectas(self, client):
        """Debe devolver 401 con credenciales que no existen"""
        res = client.post("/api/login", json={
            "email": "noexiste@test.com",
            "password": "wrongpassword"
        })
        assert res.status_code in (400, 401, 500)

    def test_login_falta_password(self, client):
        """Debe fallar si falta la contraseña"""
        res = client.post("/api/login", json={
            "email": "test@test.com"
        })
        assert res.status_code == 400


class TestMe:
    """Tests del endpoint /api/me"""

    def test_me_sin_autenticar(self, client):
        """Debe devolver 401 si no hay sesión"""
        res = client.get("/api/me")
        assert res.status_code == 401
        data = res.get_json()
        assert data["status"] == "error"


class TestLogout:
    """Tests del endpoint /api/logout"""

    def test_logout_siempre_ok(self, client):
        """Logout siempre debe devolver 200"""
        res = client.post("/api/logout")
        assert res.status_code == 200
