from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from database import models


def add_paper(db: Session, paper_data: dict) -> models.S2Papers | None:
    # Filter data to ensure no extra keys cause errors
    db_paper_data = {
        "paper_id": paper_data.get("paper_id"),
        "doi_id": paper_data.get("doi_id"),
        "arxiv_id": paper_data.get("arxiv_id"),
        "title": paper_data.get("title"),
        "abstract": paper_data.get("abstract"),
        "authors": paper_data.get("authors"),
        "year": paper_data.get("year"),
        "url": paper_data.get("url"),
        "open_access_url": paper_data.get("open_access_url"),
        "journal": paper_data.get("journal"),
    }

    stmt = (
        insert(models.S2Papers)
        .values(**db_paper_data)
        .on_conflict_do_nothing(index_elements=["paper_id"])
        .returning(models.S2Papers)
    )

    result = db.execute(stmt)
    # Fetch the result before committing, as commit() closes the cursor
    inserted_paper = result.scalar_one_or_none()
    db.commit()

    return inserted_paper
