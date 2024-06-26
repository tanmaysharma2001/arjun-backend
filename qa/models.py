from typing import List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    model:str
    text: str
    n_results: int

class GetRepoInfoRequest(BaseModel):
    repo_url: str
    lang: str

class RepoAddRequest(BaseModel):
    repo: str
