import asyncio
import threading
import typing
from bs4 import BeautifulSoup
import bs4
import requests
from qa.utils.summarize import summarize


class MoshubAPI():
    def __init__(self, model:str = "openai") -> None:
        self.model = model


    async def search_repositories(self, query: str, repos: list, n_repos: int, lang: str = "ru") -> list:
        try:
            url = "https://hub.mos.ru/explore/projects" + "?name=" + \
                query + "&sort=latest_activity_desc"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            n_found_repos = len(soup.find_all('li', class_='project-row'))
            repos_elements = soup.find_all(
                'li', class_='project-row')[:min(n_repos, n_found_repos)]

            repo_urls = [self.extract_repo_url(
                repo_element) for repo_element in repos_elements]

            search_results = []

            threads = []

            for repo_url in repo_urls:
                scraped_info = await self.scrape_info(repo_url=repo_url)

                _t = threading.Thread(
                    target=asyncio.run,
                    args=(self.process_result(
                        scraped_info, search_results, lang),),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()

            repos.extend(search_results)

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    async def scrape_info(self, repo_url) -> dict:
        soup = BeautifulSoup(requests.get(repo_url).content, 'html.parser')

        info = {}
        info["repo_url"] = repo_url

        info["repo_name"] = self.get_repo_name(info["repo_url"])

        info["license"] = None

        info["repo_owner"] = self.get_owner_name(info["repo_url"])

        for possible_readme_url in self.get_readme_urls(owner_name=info["repo_owner"], repo_name=info["repo_name"]):
            repo_readme_content = await self.get_readme_content(possible_readme_url)
            if repo_readme_content != "":
                info["readme_content"] = repo_readme_content
                break

        info["star_count"] = int(soup.find_all(
            'a', {'class': 'gl-button btn btn-default has-tooltip star-count count'})[0].text)

        return info

    def get_repo_name(self, repo_url: str) -> str:
        splits = repo_url.split("/")
        return splits[4]

    def get_owner_name(self, repo_url: str) -> str:
        splits = repo_url.split("/")
        return splits[3]

    async def get_readme_content(self, readme_url: str) -> str:
        readme = requests.get(
            url=readme_url)
        if readme.status_code == 200 and not readme.content.decode().startswith("<!DOCTYPE html>"):
            return readme.content.decode()
        print(f"Can not find readme.md for gitverse for this link: {readme_url}")
        return ""

    def get_readme_urls(self, owner_name: str, repo_name: str, ) -> typing.List[str]:
        prefix = f"https://hub.mos.ru/{owner_name}/{repo_name}/-/raw/"
        return [
            prefix + "main/README.md",
            prefix + "main/readme.md",
            prefix + "main/ReadMe.md",
            prefix + "master/README.md",
            prefix + "master/readme.md",
            prefix + "master/ReadMe.md",
            prefix + "dev/readme.md",
            prefix + "dev/README.md",
            prefix + "dev/ReadMe.md",
        ]

    def extract_repo_url(self, repo_element: bs4.element.Tag) -> str:
        return "https://hub.mos.ru" + repo_element.find_all('div', class_='project-cell gl-w-11')[0].find_all('a')[0][
            'href']

    async def process_result(self, info: dict, results: list, lang: str = "en") -> None:
        repo_name = info["repo_name"]
        repo_url = info["repo_url"]
        repo_owner = info["repo_owner"]
        repo_forks = 0
        repo_stars = info["star_count"]
        repo_description = ""
        repo_readme_content = info.get(
            "readme_content", "There is no README for this repo")

        summary = await summarize(lang, repo_readme_content, repo_description, model=self.model)

        results.append(
            {
                "name": repo_name,
                "owner": repo_owner,
                "version_control": "moshub",
                "url": repo_url,
                # "forks": repo_forks,
                "stars": repo_stars,
                # "description": repo_description,
                "readme_content": repo_readme_content,
                "summary": summary,
            }
        )

    async def get_repo_info(self, repo_url: str, lang="ru") -> dict:
        scraped_info = await self.scrape_info(repo_url)
        contributors = scraped_info["repo_owner"]
        repo_name = scraped_info["repo_name"]
        repo_url = scraped_info["repo_url"]
        repo_forks = 0
        repo_stars = scraped_info["star_count"]
        readme_content = scraped_info["readme_content"]
        summary = await summarize(lang=lang, readme_content=readme_content, description="")
        info = {
            "name": repo_name,
            "version_control": "moshub",
            "url": repo_url,
            "forks": repo_forks,
            "stars": repo_stars,
            "summary": summary,
            "contributors": contributors,
            "licence": scraped_info["license"],
        }

        return info
