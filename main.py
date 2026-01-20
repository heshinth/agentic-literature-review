from utils.s2_client import client
from rich import print

print(client.s2_search_api(query="machine learning", max_results=1))