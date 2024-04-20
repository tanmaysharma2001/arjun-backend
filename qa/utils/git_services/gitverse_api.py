from bs4 import BeautifulSoup
import httpx
import xmltodict
import asyncio
import threading
from qa.utils.summarize import summarize


class GitverseAPI():
    def __init__(self, yc_folder, yc_secret_key):
        self.yc_folder = yc_folder
        self.yc_secret_key = yc_secret_key


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

    async def scrape_info(self, gitverse_repo_url: str) -> dict:

        info = {}

        print(f"Scraping {gitverse_repo_url}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(gitverse_repo_url)
                html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            # Get title
            info["title"] = soup.findAll("h1")[0].text

            # Get forks
            forks_element = soup.find_all(string="Форк")[
                0].find_next_sibling("div")
            info["forks"] = int(forks_element.text.strip())

            # Get stars
            for span in soup.find_all("span"):
                if span.text == " В избранное":
                    stars = int(span.find_next_sibling("div").text)

            info["stars"] = stars

            info["readme_content"] = await self.get_readme_content(gitverse_repo_url)

        except Exception as e:
            raise e

        return info

    async def get_readme_content(self, gitverse_repo_url: str) -> str:

        gitverse_repo_full_name = (
            gitverse_repo_url.split("/")[3] + "/" + gitverse_repo_url.split("/")[4]
        )
        readme_content = "no readme"
        possible_branch_names = ["master", "main"]
        md_variations = ["md", "MD"]
        for branch in possible_branch_names:
            for md_variation in md_variations:
                gitverse_repo_readme_url = f"https://gitverse.ru/api/repos/{ \
                    gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
                async with httpx.AsyncClient() as client:
                    response = await client.get(gitverse_repo_readme_url)
                if response.status_code == 400:
                    continue
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
            self, result: dict, results: list, lang: str = "en"
        ) -> None:
        repo_url = await self.extract_repo_url(result["url"])

        if repo_url is not None:
            try:
                repo_info = await self.scrape_info(repo_url)
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
