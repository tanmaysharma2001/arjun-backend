from typing import List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    text: str
    n_results: int

class RepoAddRequest(BaseModel):
    repo: str
