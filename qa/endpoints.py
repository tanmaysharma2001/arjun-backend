import time

from fastapi import APIRouter
from .models import QueryRequest, RepoAddRequest, GetRepoInfoRequest
from .utils.lang_detector import detect_lang
from .utils.search import smart_search

# from .utils.search import process_github_result, process_gitverse_result, get_github_repo_info
# from .utils.database import add_repo_to_db
import urllib
from qa.utils.git_services.github_api import GithubAPI
from qa.utils.git_services.gitlab_api import GitlabAPI
from qa.utils.git_services.gitverse_api import GitverseAPI
from qa.utils.git_services.gitee_api import GiteeAPI
from qa.utils.git_services.moshub_api import MoshubAPI
from qa.utils.git_services.gitflame_api import GitFlameAPI
from qa.utils.git_services.gitflic_api import GitflicAPI
from qa.utils.git_services.launchpad_api import LaunchPadAPI

router = APIRouter()


@router.post("/query")
async def search(query: QueryRequest):
    start_time = time.time()
    lang = await detect_lang(query=query.text, model="openai")
    repos = await smart_search(
        lang["detected_language"],
        query.text,
        int(query.n_results),
        model="openai",
    )
    end_time = time.time()
    total_time = end_time - start_time
    print("Time taken to get results in seconds: " + str(total_time))
    return repos


@router.post("/get_repo_info")
async def search(query: GetRepoInfoRequest):
    repo_url = query.repo_url
    lang = query.lang

    domain = repo_url.split("/")[2]

    response = {}
    print(domain)
    if "github" in domain:
        response = await GithubAPI().get_repo_info(repo_url, lang)
    elif "gitlab" in domain:
        response = await GitlabAPI().get_repo_info(repo_url, lang)
    elif "launchpad" in domain:
        response = await LaunchPadAPI(model="openai").get_repo_info(repo_url, lang)
    elif "gitverse" in domain:
        response = await GitverseAPI().get_repo_info(repo_url, lang)
    elif "gitee" in domain:
        response = await GiteeAPI().get_repo_info(repo_url, lang)
    elif "hub.mos" in domain:
        response = await MoshubAPI().get_repo_info(repo_url, lang)
    elif "gitflame" in domain:
        response = await GitFlameAPI().get_repo_info(repo_url, lang)
    elif "gitflic" in domain:
        response = await GitflicAPI().get_repo_info(repo_url, lang)
    else:
        response = {"error": "Repo link is invalid"}

    return response


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