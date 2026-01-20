from db_config import engine, Base
import models  # noqa: F401 (to silence unused import warning)

def create_tables():
    Base.metadata.create_all(bind=engine)