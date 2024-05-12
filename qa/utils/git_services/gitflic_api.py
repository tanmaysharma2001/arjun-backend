from bs4 import BeautifulSoup
import httpx
import xmltodict
import asyncio
import threading
from qa.utils.summarize import summarize
from dotenv import load_dotenv, find_dotenv
import os


class GitflicAPI():
    def __init__(self, model:str = "openai"):
        load_dotenv(find_dotenv())
        self.yc_folder = os.getenv("YC_FOLDER")
        self.yc_secret_key = os.getenv("YC_SECRET")
        self.model = model


    async def search_repositories(self, query: str, repos: list, lang: str = "en"):
        url = "https://yandex.ru/search/xml"
        params = {
            "folderid": self.yc_folder,
            "apikey": self.yc_secret_key,
        }
        results = []
        async with httpx.AsyncClient(timeout=10) as client:
            params["query"] = query + " host:gitverse.ru"
            response = await client.get(url, params=params)
            data_dict = xmltodict.parse(response.text)
            try:
                _res = data_dict["yandexsearch"]["response"]["results"]["grouping"][
                    "group"
                ]["doc"]
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
                    args=(self.process_result(result, results, lang),),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()

        repos.extend(results)

    async def scrape_info(self, gitflic_repo_url: str) -> dict:

        info = {}

        print(f"Scraping {gitflic_repo_url}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(gitflic_repo_url)
                html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            # Get name
            info["name"] = gitflic_repo_url.split('/')[5]

            # Get forks
            forks_element = soup.find_all(class_="text-muted")
            info["forks"] = int(forks_element[5].text.strip().split('\n')[0])


            info["stars"] = int(forks_element[6].text.strip().split('\n')[0])

            info["readme_content"] = await self.get_readme_content(gitflic_repo_url)
            info['license'] = ""
            info['contributors'] = [gitflic_repo_url.split('/')[4]]

            h4_tag = soup.find('p', class_='project__project-desc-text')

            if h4_tag:
                info["description"] = h4_tag.text
            else:
                info["description"] = ""

        except Exception as e:
            raise e

        return info

    async def get_readme_content(self, gitflic_repo_url: str) -> str:
        readme_content = ""

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(gitflic_repo_url + "#readme")
            readme_content = response.text

        return readme_content

    async def extract_repo_url(self, file_url: str) -> str:
        # Split the URL into parts
        parts = file_url.split("/")
        # Check if the URL is valid and contains enough parts to extract the repo URL
        if len(parts) >= 5:
            # Reconstruct the repo URL
            repo_url = "/".join(parts[:5])
            return repo_url
        else:
            return None

    async def process_result(
        self, yandex_search_result: dict, results: list, lang: str = "ru"
    ) -> None:
        repo_url = await self.extract_repo_url(yandex_search_result["url"])

        if repo_url is not None:
            try:
                repo_info = await self.scrape_info(repo_url)
                repo_name = repo_info["name"]
                forks = repo_info["forks"]
                stars = repo_info["stars"]
                readme_content = repo_info["readme_content"]
                description = yandex_search_result.get("headline")
                contributors = repo_info.get("contributors", [])
                summary = await summarize(lang, readme_content, description, model=self.model)
                results.append(
                    {
                        "name": repo_name,
                        "version_control": "gitverse",
                        "url": repo_url,
                        "forks": forks,
                        "stars": stars,
                        "license": repo_info['license'],
                        "description": description,
                        "readme_content": readme_content,
                        'contributors': contributors,
                        "summary": summary,
                    }
                )
            except Exception as e:
                print(f"Error occurred while scraping {repo_url}. Details:", e)

    async def get_repo_info(self, repo_url: str, lang: str) -> dict:
        data = await self.scrape_info(repo_url)
        repo_license = data['license']
        repo_name = data["name"]
        repo_forks = data["forks"]
        repo_stars = data["stars"]
        repo_contributors = data['contributors']
        repo_description = data["description"]
        repo_readme_content = await self.get_readme_content(repo_url)
        if repo_readme_content == "README not found or access denied.":
            repo_readme_content = "There is no README for this repo"

        summary = await summarize(lang, repo_readme_content, repo_description, model=self.model)

        info = {
            "name": repo_name,
            "version_control": "gitflic",
            "url": repo_url,
            "forks": repo_forks,
            "stars": repo_stars,
            "licence": repo_license,
            "summary": summary,
            "contributors" : repo_contributors,
        }
        return info