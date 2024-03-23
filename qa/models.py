from typing import List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    text: str

