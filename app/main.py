from utils.s2_client import client
from rich import print
from database.create_tables import create_tables

create_tables()

print(client.s2_search_api(query="machine learning in 2026", max_results=3))