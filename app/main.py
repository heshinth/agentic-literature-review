from utils.s2_client import client
from database.create_tables import create_tables
from database.crud import add_paper
from database.db_config import SessionLocal

from logging_config import get_logger

logger = get_logger(__name__)

create_tables()


search_query = input("Enter your search query: ")
result = client.s2_search_api(query=search_query, max_results=3)

with SessionLocal() as db:
    for paper_data in result:
        paper = add_paper(db, paper_data)
        if paper:
            logger.info(f"Added paper: {paper.title} ({paper.year})")
        else:
            logger.info(f"Skipped existing paper:{paper_data.get('title')}")