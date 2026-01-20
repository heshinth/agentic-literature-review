from utils.s2_client import client
from rich import print
from database.create_tables import create_tables
from database.crud import add_paper
from database.db_config import SessionLocal

create_tables()


search_query = "machine learning in 2026"
result = client.s2_search_api(query=search_query, max_results=3)

with SessionLocal() as db:
    for paper_data in result:
        paper = add_paper(db, paper_data)
        if paper:
            print(f"Added paper: [bold]{paper.title}[/bold] ({paper.year})")
        else:
            print(f"Skipped existing paper: [dim]{paper_data.get('title')}[/dim]")
