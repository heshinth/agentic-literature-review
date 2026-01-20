from database.db_config import engine, Base
import database.models  # noqa: F401 (to silence unused import warning)

def create_tables():
    Base.metadata.create_all(bind=engine)