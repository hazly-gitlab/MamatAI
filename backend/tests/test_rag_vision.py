import pytest
import io
from httpx import AsyncClient, ASGITransport
from app.rag.vector_index import add_to_index, search_index

@pytest.mark.asyncio
async def test_rag_vector_search():
    add_to_index(document_id=99, filename="security_policy.pdf", text="All administrative sessions must enforce multi-factor authentication.")
    results = search_index("multi-factor authentication")
    assert len(results) > 0
    assert results[0]["filename"] == "security_policy.pdf"

@pytest.mark.asyncio
async def test_vision_analysis_api(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/v1/auth/register", json={
            "username": "vis_user",
            "email": "vis_user@jarvis.ai",
            "password": "DefaultPassword123!",
            "role": "user"
        })
        login_res = await ac.post("/api/v1/auth/login", data={
            "username": "vis_user",
            "password": "DefaultPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        fake_image = io.BytesIO(b"MOCK_PNG_IMAGE_BYTES")
        files = {"file": ("screenshot.png", fake_image, "image/png")}
        data = {"query": "Explain this error in the screenshot"}

        res = await ac.post("/api/v1/vision/analyse", files=files, data=data, headers=headers)
        assert res.status_code == 200
        assert "analysis" in res.json()
