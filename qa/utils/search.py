import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import httpx
import xmltodict
import asyncio
import threading
import urllib
from qa.utils.rank import rank_repositories

API_KEY = os.getenv("SERP_API")
YC_FOLDER = os.getenv("YC_FOLDER")
YC_SECRET_KEY = os.getenv("YC_SECRET")

load_dotenv(find_dotenv())

GIT_TOKEN = os.environ["GIT_TOKEN"]

from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries
from qa.utils.summarize import summarize


async def smart_search(lang, query, n_results):
    en_queries = await generate_queries('en', query)
    en_keywords = await generate_keywords('en', en_queries)

    ru_queries = await generate_queries('ru', query)
    ru_keywords = await generate_keywords('ru', ru_queries)

    repositories = []
    threads = []
    for i in range(len(min(en_keywords, ru_keywords))):
        
        # Github
        _t = threading.Thread(
            target=asyncio.run,

            # Search in english only because github api doesn't provide good results for russian keywords
            args=(search_github_repositories(en_keywords[i], repositories, lang),),
        )
        threads.append(_t)
        _t.start()

        # Gitverse
        _t = threading.Thread(
            target=asyncio.run,
            args=(search_gitverse_repositories(
                en_keywords[i] if lang == 'en' else ru_keywords[i], repositories, lang),),
        )
        threads.append(_t)
        _t.start()


    for thread in threads:
        thread.join()

    # readme_content and description are not necessary anymore
    for repo in repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)
    

    # Remove duplicate repos
    done = set()
    unique_repos = []
    for repo in repositories:
        if repo['url'] not in done:
            done.add(repo['url'])
            unique_repos.append(repo)

    # Get top ranked repositories
    ranked_repositories = rank_repositories(query, unique_repos, n_results)

    return ranked_repositories


async def process_github_result(result: dict, results: list, lang: str = "en") -> None:
    repo_name = result["name"]
    repo_url = result["html_url"]
    repo_forks = result["forks_count"]
    repo_stars = result["stargazers_count"]
    repo_description = result["description"]
    repo_readme_content = await get_readme_content_github(result["full_name"])
    if repo_readme_content == "README not found or access denied.":
        repo_readme_content = repo_description

    # TODO
    summary = await summarize(lang, repo_readme_content, repo_description)

    results.append(
        {
            "name": repo_name,
            "version_control": "github",
            "url": repo_url,
            "forks": repo_forks,
            "stars": repo_stars,
            "description": repo_description,
            "readme_content": repo_readme_content,
            "summary": summary,
        }
    )


async def search_github_repositories(query, repos: list, lang: str = "en"):

    print(query)

    url = "https://api.github.com/search/repositories"
    stars = "100"
    license = "mit"
    forks = "100"

    per_page = 10

    payload = {}
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GIT_TOKEN}",
    }

    params = {
        "q": query,
        "stars": stars,
        "license": license,
        "forks": forks,
        "per_page": per_page,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            data = response.json()

        repositories = []
        threads = []

        for item in data.get("items", []):
            _t = threading.Thread(
                target=asyncio.run,
                args=(process_github_result(item, repositories, lang),),
            )
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()

        repos.extend(repositories)
    except Exception as e:
        print("Error occurred:", e)


async def get_readme_content_github(full_name):
    print(full_name)
    url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",
        "Authorization": f"token {GIT_TOKEN}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return "README not found or access denied."


async def process_gitverse_result(
    result: dict, results: list, lang: str = "en"
) -> None:
    repo_url = await extract_gitverse_repo_url(result["url"])

    if repo_url is not None:
        try:
            repo_info = await scrape_gitverse(repo_url)
            title = repo_info["title"]
            forks = repo_info["forks"]
            stars = repo_info["stars"]
            readme_content = repo_info["readme_content"]

            summary = await summarize(lang, readme_content, result.get("headline"))
            results.append(
                {
                    "name": title,
                    "version_control": "gitverse",
                    "url": repo_url,
                    "forks": forks,
                    "stars": stars,
                    "description": result.get("headline"),
                    "readme_content": readme_content,
                    "summary": summary,
                }
            )
        except Exception as e:
            print(f"Error occurred while scraping {repo_url}. Details:", e)


async def search_gitverse_repositories(query: str, repos: list, lang: str = "en"):
    url = "https://yandex.ru/search/xml"
    params = {
        "folderid": YC_FOLDER,
        "apikey": YC_SECRET_KEY,
    }
    results = []
    async with httpx.AsyncClient() as client:
        params["query"] = query + " host:gitverse.ru"
        response = await client.get(url, params=params)
        data_dict = xmltodict.parse(response.text)
        try:
            _res = data_dict["yandexsearch"]["response"]["results"]["grouping"]["group"]["doc"]
        except KeyError:
            print(data_dict)
            _res = []
        except TypeError:
            _res = data_dict["yandexsearch"]["response"]["results"]["grouping"]["group"]
        
        threads = []
        
        for result in _res:
            if "doc" in result.keys():
                result = result["doc"]
            _t = threading.Thread(
                target=asyncio.run,
                args=(process_gitverse_result(result, results, lang),),
            )
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()

    repos.extend(results)


async def scrape_gitverse(gitverse_repo_url: str) -> dict:

    info = {}

    print(f"Scraping {gitverse_repo_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(gitverse_repo_url)
            html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")

        # Get title
        info["title"] = soup.findAll("h1")[0].text

        # Get forks
        forks_element = soup.find_all(string="Форк")[0].find_next_sibling("div")
        info["forks"] = int(forks_element.text.strip())

        # Get stars
        for span in soup.find_all("span"):
            if span.text == " В избранное":
                stars = int(span.find_next_sibling("div").text)

        info["stars"] = stars

        info["readme_content"] = await get_readme_content_gitverse(gitverse_repo_url)

    except Exception as e:
        raise e

    return info


async def get_readme_content_gitverse(gitverse_repo_url: str) -> str:

    gitverse_repo_full_name = (
        gitverse_repo_url.split("/")[3] + "/" + gitverse_repo_url.split("/")[4]
    )
    readme_content = "no readme"
    possible_branch_names = ["master", "main"]
    md_variations = ["md", "MD"]
    for branch in possible_branch_names:
        for md_variation in md_variations:
            gitverse_repo_readme_url = f"https://gitverse.ru/api/repos/{gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
            async with httpx.AsyncClient() as client:
                response = await client.get(gitverse_repo_readme_url)
            if response.status_code == 400:
                continue
            readme_content = response.text

    return readme_content


async def extract_gitverse_repo_url(file_url: str) -> str:
    # Split the URL into parts
    parts = file_url.split("/")
    # Check if the URL is valid and contains enough parts to extract the repo URL
    if len(parts) >= 5:
        # Reconstruct the repo URL
        repo_url = "/".join(parts[:5])
        return repo_url
    else:
        return None


async def get_github_repo_info(repo_url: str) -> dict:
    # extract the owner and repo name
    url = urllib.parse.urlparse(repo_url)
    path = url.path.split("/")
    owner = path[1]
    repo = path[2]
    # construct the API URL
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    # make the request
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()
    return data
