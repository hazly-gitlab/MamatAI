import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.app.core.database import Base, engine, AsyncSessionLocal
from backend.app.models.models import User, UserRole, ToolSetting
from backend.app.security.password import hash_password

async def init_models():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if Admin already exists
        result = await session.execute(select(User).where(User.role == UserRole.ADMINISTRATOR))
        admin = result.scalars().first()

        if not admin:
            hashed_pw = hash_password("admin123")
            admin_user = User(
                email="admin@jarvis.ai",
                hashed_password=hashed_pw,
                full_name="System Administrator",
                role=UserRole.ADMINISTRATOR,
                is_active=True
              )
            session.add(admin_user)
            print("Default administrator seeded: admin@jarvis.ai / admin123")

        # Seed initial tools
        initial_tools = [
            {"name": "web_search", "description": "Search the web for up to date information.", "enabled": True, "requires_confirmation": False, "permission_level": "user"},
            {"name": "calculator", "description": "Solve mathematical expressions safely.", "enabled": True, "requires_confirmation": False, "permission_level": "user"},
            {"name": "get_weather", "description": "Fetch real-time weather details for a specific city.", "enabled": True, "requires_confirmation": False, "permission_level": "user"},
            {"name": "safe_sql_query", "description": "Run read-only analytical SQL queries on approved databases.", "enabled": True, "requires_confirmation": True, "permission_level": "user"},
            {"name": "http_request", "description": "Perform HTTP GET/POST queries to approved external allowlisted domains.", "enabled": True, "requires_confirmation": True, "permission_level": "user"},
            {"name": "system_status", "description": "Retrieve CPU, memory, database, and Redis usage statistics.", "enabled": True, "requires_confirmation": False, "permission_level": "user"},
            {"name": "delete_document", "description": "Delete uploaded documents from memory and vector store.", "enabled": True, "requires_confirmation": True, "permission_level": "user"}
        ]

        for tool_data in initial_tools:
            res = await session.execute(select(ToolSetting).where(ToolSetting.name == tool_data["name"]))
            existing_tool = res.scalars().first()
            if not existing_tool:
                tool = ToolSetting(**tool_data)
                session.add(tool)
                print(f"Seeded tool: {tool_data['name']}")

        await session.commit()
    print("Seeding completed successfully.")

async def main():
    await init_models()
    await seed_data()

if __name__ == "__main__":
    asyncio.run(main())
