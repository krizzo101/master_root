from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_async_engine(DATABASE_URL, future=True, echo=False)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_session() -> AsyncSession:
    async def _get_session():
        async with async_session_maker() as session:
            yield session

    return _get_session()
