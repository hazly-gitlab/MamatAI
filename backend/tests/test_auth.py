import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_resp = await ac.post("/api/v1/auth/register", json={
            "username": "test_admin",
            "email": "test_admin@jarvis.ai",
            "password": "DefaultPassword123!",
            "role": "admin"
        })
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        assert data["username"] == "test_admin"
        assert data["role"] == "admin"

        login_resp = await ac.post("/api/v1/auth/login", data={
            "username": "test_admin",
            "password": "DefaultPassword123!"
        })
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["username"] == "test_admin"
        assert token_data["role"] == "admin"
