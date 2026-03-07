from database.db_config import engine, Base
from sqlalchemy import text
import database.models  # noqa: F401 (to silence unused import warning)


def create_tables():
    Base.metadata.create_all(bind=engine)

    # Backfill for existing databases where s2_papers was created before new fields.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE s2_papers
                ADD COLUMN IF NOT EXISTS is_downloaded BOOLEAN NOT NULL DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_extracted BOOLEAN NOT NULL DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_embedded BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS paper_texts (
                    paper_id VARCHAR PRIMARY KEY REFERENCES s2_papers(paper_id) ON DELETE CASCADE,
                    full_text TEXT NOT NULL
                )
                """
            )
        )
