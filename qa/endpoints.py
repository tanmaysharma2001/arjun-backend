from fastapi import APIRouter
from .models import QueryRequest
from .utils.lang_detector import detect_lang
from .utils.search import smart_search

router = APIRouter()


@router.post("/query")
async def search(query: QueryRequest):
    lang = detect_lang(query=query.text)
    repos = await smart_search(lang, query.text)
    return repos
