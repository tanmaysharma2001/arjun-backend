import requests
import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import httpx
import xmltodict

API_KEY = os.getenv("SERP_API")
YC_FOLDER = os.getenv("YC_FOLDER")
YC_SECRET_KEY = os.getenv("YC_SECRET")

load_dotenv(find_dotenv())

GIT_TOKEN = os.environ["GIT_TOKEN"]

from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries


async def smart_search(lang, query):
    queries = generate_queries(lang, query)
    keywords = generate_keywords(lang, queries)
    repositories = []
    for keyword in keywords:
        github_repos = search_github_repositories(keyword)
        repositories.extend(github_repos)
        gitverse_repos = await search_gitverse_repositories(keyword)
        repositories.extend(gitverse_repos)


    return repositories


def search_github_repositories(query):

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
        response = requests.request(
            "GET", url, headers=headers, data=payload, params=params
        )
        data = response.json()

        repositories = []

        for item in data.get("items", []):
            repo_name = item.get("name")
            repo_url = item.get("html_url")
            repo_forks = item.get("forks_count")
            repo_stars = item.get("stargazers_count")
            repo_full_name = item.get("full_name")
            repo_description = item.get("description")
            repo_readme_content = get_readme_content_github(repo_full_name) if get_readme_content_github(repo_full_name) \
                != "README not found or access denied." \
                    else repo_description

            repositories.append(
                {
                    "name": repo_name,
                    "version_control": "github",
                    "url": repo_url,
                    "forks": repo_forks,
                    "stars": repo_stars,
                    "description": repo_description,
                    "readme_content": repo_readme_content,
                }
            )

        return repositories
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
        return []


def get_readme_content_github(full_name):
    print(full_name)
    url = f"https://api.github.com/repos/{full_name}/readme"
    github_token = "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"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",
        "Authorization": f"token {github_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return "README not found or access denied."


async def search_gitverse_repositories(query: str):
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
        for result in _res:
            doc = result["doc"]
            repo_url = extract_gitverse_repo_url(doc["url"])

            if repo_url is not None:
                try: 
                    repo_info = scrape_gitverse(repo_url)
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

    return results

def scrape_gitverse(gitverse_repo_url: str) -> dict:
    info = {}

    print(f"Scraping {gitverse_repo_url}")
    try:
        html_content = requests.get(gitverse_repo_url).text

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

        info['readme_content'] = get_readme_content_gitverse(gitverse_repo_url)

    except Exception as e:
        raise e

    return info


def get_readme_content_gitverse(gitverse_repo_url: str) -> str:
    gitverse_repo_full_name = gitverse_repo_url.split(
        "/")[3] + "/" + gitverse_repo_url.split("/")[4]
    readme_content = "no readme"
    possible_branch_names = ["master", "main"]
    md_variations = ["md", "MD"]
    for branch in possible_branch_names:
        for md_variation in md_variations:
            gitverse_repo_readme_url = \
                f"https://gitverse.ru/api/repos/{gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
            response = requests.get(gitverse_repo_readme_url)
            if response.status_code == 400:
                continue
            readme_content = response.text

    return readme_content


def extract_gitverse_repo_url(file_url: str) -> str:
    # Split the URL into parts
    parts = file_url.split('/')
    # Check if the URL is valid and contains enough parts to extract the repo URL
    if len(parts) >= 5:
        # Reconstruct the repo URL
        repo_url = '/'.join(parts[:5])
        return repo_url
    else:
        return None