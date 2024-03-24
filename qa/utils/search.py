import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import httpx
import xmltodict
import asyncio
import threading

API_KEY = os.getenv("SERP_API")
YC_FOLDER = os.getenv("YC_FOLDER")
YC_SECRET_KEY = os.getenv("YC_SECRET")

load_dotenv(find_dotenv())

GIT_TOKEN = os.environ["GIT_TOKEN"]

from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries


async def smart_search(lang, query):
    queries = await generate_queries(lang, query)
    keywords = await generate_keywords(lang, queries)
    repositories = []
    threads = []
    for keyword in keywords:
        _t = threading.Thread(target=asyncio.run, args=(search_github_repositories(keyword, repositories),))
        threads.append(_t)
        _t.start()
        _t = threading.Thread(target=asyncio.run, args=(search_gitverse_repositories(keyword, repositories),))
        threads.append(_t)
        _t.start()

    for thread in threads:
        thread.join()


    return repositories

async def process_github_result(result: dict, results: list) -> None:
    repo_name = result["name"]
    repo_url = result["html_url"]
    repo_forks = result["forks_count"]
    repo_stars = result["stargazers_count"]
    repo_description = result["description"]
    repo_readme_content = await get_readme_content_github(result["full_name"])
    if repo_readme_content == "README not found or access denied.":
        repo_readme_content = repo_description

    results.append({
        "name": repo_name,
        "version_control": "github",
        "url": repo_url,
        "forks": repo_forks,
        "stars": repo_stars,
        "description": repo_description,
        "readme_content": repo_readme_content,
    })

async def search_github_repositories(query, repos: list):

    print(query)
    await asyncio.sleep(0.001)

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
            _t = threading.Thread(target=asyncio.run, args=(process_github_result(item, repositories),))
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()    

        repos.extend(repositories)
    except Exception as e:
        print("Error occurred:", e)


async def get_readme_content_github(full_name):
    await asyncio.sleep(0.001)
    print(full_name)
    url = f"https://api.github.com/repos/{full_name}/readme"
    github_token = "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"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",
        "Authorization": f"token {github_token}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return "README not found or access denied."

async def process_gitverse_result(result: dict, results: list) -> None:
    doc = result["doc"]
    repo_url = await extract_gitverse_repo_url(doc["url"])

    if repo_url is not None:
        try: 
            repo_info = await scrape_gitverse(repo_url)
            title = repo_info['title']
            forks = repo_info['forks']
            stars = repo_info['stars']
            readme_content = repo_info['readme_content']

            results.append({
                "name": title,
                "version_control": "gitverse",
                "url": repo_url,
                "forks": forks,
                "stars": stars,
                "description": doc.get("headline"),
                "readme_content": readme_content,
            })
        except Exception as e:
            print(f"Error occurred while scraping {repo_url}. Details:", e)

async def search_gitverse_repositories(query: str, repos: list):
    await asyncio.sleep(0.001)

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
            _res = data_dict["yandexsearch"]["response"]["results"]["grouping"]["group"]
        except KeyError:
            print(data_dict)
            _res = []
        threads = []
        for result in _res:
            _t = threading.Thread(target=asyncio.run, args=(process_gitverse_result(result, results),))
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()

    repos.extend(results)

async def scrape_gitverse(gitverse_repo_url: str) -> dict:
    await asyncio.sleep(0.001)

    info = {}

    print(f"Scraping {gitverse_repo_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(gitverse_repo_url)
            html_content = response.text     

        soup = BeautifulSoup(html_content, 'html.parser')

        # Get title
        info['title'] = soup.findAll('h1')[0].text

        # Get forks
        forks_element = soup.find_all(string="Форк")[0].find_next_sibling("div")
        info['forks'] = int(forks_element.text.strip())

        # Get stars
        for span in soup.find_all('span'):
            if span.text == " В избранное":
                stars = int(span.find_next_sibling("div").text)

        info['stars'] = stars

        info['readme_content'] = await get_readme_content_gitverse(gitverse_repo_url)

    except Exception as e:
        raise e

    return info


async def get_readme_content_gitverse(gitverse_repo_url: str) -> str:
    await asyncio.sleep(0.001)

    gitverse_repo_full_name = gitverse_repo_url.split(
        "/")[3] + "/" + gitverse_repo_url.split("/")[4]
    readme_content = "no readme"
    possible_branch_names = ["master", "main"]
    md_variations = ["md", "MD"]
    for branch in possible_branch_names:
        for md_variation in md_variations:
            gitverse_repo_readme_url = \
                f"https://gitverse.ru/api/repos/{gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
            async with httpx.AsyncClient() as client:
                response = await client.get(gitverse_repo_readme_url)
            if response.status_code == 400:
                continue
            readme_content = response.text

    return readme_content


async def extract_gitverse_repo_url(file_url: str) -> str:
    await asyncio.sleep(0.001)
    # Split the URL into parts
    parts = file_url.split('/')
    # Check if the URL is valid and contains enough parts to extract the repo URL
    if len(parts) >= 5:
        # Reconstruct the repo URL
        repo_url = '/'.join(parts[:5])
        return repo_url
    else:
        return None