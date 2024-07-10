from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from asyncpg.exceptions import DuplicateDatabaseError
from sqlalchemy.exc import OperationalError
from sqlalchemy.dialects.postgresql import UUID

from backend.app.core.logging import logger
from backend.app.database.models.base import Base


class Database:
    """
    This class represents a database connection and session management object.
    It contains two attributes:

    - engine: A callable that represents the database engine.
    - session_maker: A callable that represents the session maker.
    """

    def __init__(self, uri):
        self.uri = uri
        self.engine = create_async_engine(
            uri,
            future=True,               # Use the new asyncio-based execution strategy
            pool_size=20,              # Adjust pool size based on your workload
            max_overflow=10,           # Adjust maximum overflow connections
            pool_recycle=3600,         # Periodically recycle connections (optional)
            pool_pre_ping=True,        # Check the connection status before using it (optional)
        )
        self.session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_database(self):
        # Create the database if it does not exist
        async def create_database_alias():
            # Split the URI to get the database name
            database_name = self.uri.split("/")[-1]
            uri_without_database = '/'.join(self.uri.split("/")[:-1])
            
            # Create a new engine without specifying a database
            engine = create_async_engine(
                uri_without_database,
                future=True,               # Use the new asyncio-based execution strategy
                pool_size=20,              # Adjust pool size based on your workload
                max_overflow=10,           # Adjust maximum overflow connections
                pool_recycle=3600,         # Periodically recycle connections (optional)
                pool_pre_ping=True,        # Check the connection status before using it
            )

            # Create a new connection to execute the CREATE DATABASE statement
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("COMMIT"))
                    await conn.execute(text(f"CREATE DATABASE {database_name}"))
                    logger.info(f"Database '{database_name}' created successfully.")
            except DuplicateDatabaseError:
                logger.warning(f"Database '{database_name}' already exists.")

        await try_do(create_database_alias, "creating database")

    async def test_connection(self):
        try:
            async with self.engine.connect() as conn:
                query = text("SELECT 1")

                # Test the connection
                await conn.execute(query)

                logger.info("Connection to the database established!")
        except Exception as e:
            logger.error(f"Error connecting to the database: {str(e)}")
            

    async def create_tables(self):
        """
        Connects to a PostgreSQL database using environment variables for connection details.

        Returns:
            Database: A NamedTuple with engine and conn attributes for the database connection.
            None: If there was an error connecting to the database.

        """
        async def create_tables_alias():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Print available tables
            logger.info(f"Tables created: {Base.metadata.tables}")

    async def print_tables(self):
        """
        Print the available tables in the database.
        """
        try:
            async with self.engine.connect() as conn:
                # Use a synchronous context to run the inspector
                result = await conn.run_sync(self.get_tables)
                logger.info(f"Available tables: {result}")
        except Exception as e:
            logger.error(f"Error fetching table names: {str(e)}")


    async def init(self):
        """
        Initializes the database connection and creates the tables.

        Args:
            uri (str): The database URI.

        Returns:
            Database: A NamedTuple with engine and conn attributes for the database connection.
            None: If there was an error connecting to the database.
        """
        await self.create_database()
        await self.test_connection()
        await self.create_tables()
        await self.print_tables()

