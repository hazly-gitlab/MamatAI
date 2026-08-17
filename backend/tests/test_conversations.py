import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_conversation_and_tool_calling(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/v1/auth/register", json={
            "username": "conv_user",
            "email": "conv_user@jarvis.ai",
            "password": "DefaultPassword123!",
            "role": "admin"
        })
        login_res = await ac.post("/api/v1/auth/login", data={
            "username": "conv_user",
            "password": "DefaultPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        c_res = await ac.post("/api/v1/conversations?title=Test%20Chat", headers=headers)
        assert c_res.status_code == 200
        cid = c_res.json()["id"]

        list_res = await ac.get("/api/v1/conversations", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        stream_res = await ac.post(
            f"/api/v1/conversations/{cid}/messages/stream",
            data={"prompt": "Calculate 25 * 4"},
            headers=headers
        )
        assert stream_res.status_code == 200
        content = stream_res.text
        assert "message_complete" in content or "tool_result" in content
