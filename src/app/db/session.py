from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.utils.config import settings

# Create Async Engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create Async Session Factory
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Dependency for API Routers
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session