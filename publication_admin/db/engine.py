from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from publication_admin.settings import settings

engine = create_async_engine(settings.database.db_connection)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
