from fastapi import APIRouter
from .models import QueryRequest, RepoAddRequest
from .utils.lang_detector import detect_lang
from .utils.search import smart_search
# from .utils.search import process_github_result, process_gitverse_result, get_github_repo_info
from .utils.database import add_repo_to_db
import urllib

router = APIRouter()


@router.post("/query")
async def search(query: QueryRequest):
    lang = await detect_lang(query=query.text)
    repos = await smart_search(lang, query.text, int(query.n_results))
    return repos

# @router.post("/add-repo")
# async def add_repo(repo: RepoAddRequest):
#     url = urllib.parse.unquote(repo.repo)
#     # check if the url is a github repo
#     result = []
#     if "github.com" in url:
#         await process_github_result(await get_github_repo_info(url), result)
#     elif "gitverse.ru" in url:
#         await process_gitverse_result({"url": url}, result)
#     res = result[0]
#     add_repo_to_db(res)
#     return res