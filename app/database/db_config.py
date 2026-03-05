from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from logging_config import get_logger
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = get_logger(__name__)

# Fetch variables
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")

# Construct the SQLAlchemy connection string
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT,
    database=DBNAME,
    # Local postgres doesn't require SSL. Uncomment if using a remote service like Supabase
    # query={"sslmode": "require"},
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, poolclass=NullPool)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# Test the connection
try:
    with engine.connect() as connection:
        logger.info("Connection successful!")
except Exception as e:
    logger.error(f"Failed to connect: {e}")
