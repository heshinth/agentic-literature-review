import httpx
import os

class S2Client:
    def __init__(self, api_key: str):
        self.api_key = api_key or os.getenv("S2_API_KEY")

        if not self.api_key:
            raise ValueError("S2_API_KEY not set")

        self.client = httpx.Client(
            base_url="https://api.semanticscholar.org/graph/v1",
            headers={"x-api-key": self.api_key},
            timeout=30.0,
        )

    pass
