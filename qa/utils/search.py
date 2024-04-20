from qa.utils.git_services.github_api import GithubAPI
from qa.utils.git_services.gitverse_api import GitverseAPI
from qa.utils.git_services.gitlab_api import GitlabAPI
from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries
from qa.utils.summarize import get_final_summary
from qa.utils.rank import rank_repositories
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import os
import httpx
import xmltodict
import asyncio
import threading
import math

YC_FOLDER = os.getenv("YC_FOLDER")
YC_SECRET_KEY = os.getenv("YC_SECRET")

load_dotenv(find_dotenv())

GITHUB_ACCESS_TOKEN = os.environ["GITHUB_ACCESS_TOKEN"]
GITLAB_ACCESS_TOKEN = os.environ["GITLAB_ACCESS_TOKEN"]


async def smart_search(lang, query, n_results):
    github_api = GithubAPI(GITHUB_ACCESS_TOKEN)
    gitverse_api = GitverseAPI(YC_FOLDER, YC_SECRET_KEY)
    gitlab_api = GitlabAPI(GITLAB_ACCESS_TOKEN)

    en_queries = await generate_queries("en", query)
    en_keywords = await generate_keywords("en", en_queries)

    ru_queries = await generate_queries("ru", query)
    ru_keywords = await generate_keywords("ru", ru_queries)

    github_repositories = []
    gitverse_repositories = []
    gitlab_repositories = []
    threads = []
    for i in range(min(len(en_keywords), len(ru_keywords))):

        # Github
        _t = threading.Thread(
            target=asyncio.run,
            # Search in english only because github api doesn't provide good results for russian keywords
            args=(
                github_api.search_repositories(
                    en_keywords[i], github_repositories, lang),
            ),
            daemon=True,
        )
        threads.append(_t)
        _t.start()

        # Gitverse
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitverse_api.search_repositories(
                    ru_keywords[i],
                    gitverse_repositories,
                    lang,
                ),
            ),
            daemon=True,
        )
        threads.append(_t)
        _t.start()

        # Gitlab
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitlab_api.search_repositories(
                    en_keywords[i] if lang == "en" else ru_keywords[i],
                    gitlab_repositories,
                    lang,
                ),
            ),
            daemon=True,
        )

        threads.append(_t)
        _t.start()

    for thread in threads:
        thread.join()

    # readme_content and description are not necessary anymore
    for repo in github_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in gitverse_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in gitlab_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    # get only the unique repositories from each version control
    github_repositories=get_unique_repos(github_repositories)
    gitverse_repositories=get_unique_repos(gitverse_repositories)
    gitlab_repositories=get_unique_repos(gitlab_repositories)

    final_result = []

    # Get top ranked github repositories
    if github_repositories:
        ranked_github_repositories = rank_repositories(
            query, github_repositories, math.floor(n_results * 0.5)
        )
        final_result.append(ranked_github_repositories)
    
    # Get top ranked gitverse repositories
    if gitverse_repositories:
        ranked_gitverse_repositories = rank_repositories(
            query, github_repositories, math.floor(n_results * 0.2)
        )
        final_result.append(ranked_gitverse_repositories)

    # Get top ranked github repositories
        if gitlab_repositories:
            ranked_gitlab_repositories = rank_repositories(
                query, github_repositories, math.floor(n_results * 0.3)
            )
            final_result.append(ranked_gitlab_repositories)

    if final_result:
        summary = await get_final_summary(ranked_repositories=final_result)

        return {"summary": summary, "sources": final_result}
    
    else:
        return {"summary": "No results found", "sources": []}

def get_unique_repos(repositories: list):
    done = set()
    result = []
    for repo in repositories:
        if repo["url"] not in done:
            done.add(repo["url"])
            result.append(repo)
    return result