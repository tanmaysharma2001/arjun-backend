import os
import asyncio
import threading
import typing
import requests

from qa.utils.summarize import summarize


class GitFlameAPI():

    async def search_repositories(self, query: str, results: list, n_repos: int, lang: str = "ru") -> list:
        try:
            repositories = requests.get(
                url=self.search_url(),
                params={
                    "page": 1,
                    "limit": n_repos,
                    "q": query,
                    "is_private": False,
                })

            search_results = []
            threads = []

            for repo_data_dict in repositories.json():
                scraped_info = await self.scrape_info(repo_data_dict=repo_data_dict)

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

            results.extend(search_results)

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def search_url(self) -> str:
        return "https://gitflame.ru/api/v1/repos" + "/search"

    def get_readme_urls(self, repo_link: str) -> typing.List[str]:
        prefix = f"{repo_link}/raw//"
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

    async def get_readme_content(self, readme_url: str) -> str:
        readme = requests.get(
            url=readme_url)
        if readme.status_code == 200 and not readme.content.decode().startswith("<!DOCTYPE html>"):
            return readme.content.decode()
        print(f"Can not find readme.md for gitflame for this link: {
              readme_url}")
        return ""

    async def scrape_info(self, repo_data_dict: dict) -> dict:

        info = {}

        info["repo_url"] = repo_data_dict["html_url"]

        info["repo_name"] = repo_data_dict["name"]

        info["repo_owner"] = repo_data_dict["owner"]["username"]

        for possible_readme_url in self.get_readme_urls(repo_link=info["repo_url"]):
            repo_readme_content = await self.get_readme_content(possible_readme_url)
            if repo_readme_content != "":
                info["readme_content"] = repo_readme_content
                break

        info["description"] = repo_data_dict["description"]
        info["stars_count"] = repo_data_dict["stars_count"]
        info["forks_count"] = repo_data_dict["forks_count"]

        return info

    async def process_result(self, info: dict, results: list, lang: str = "en") -> None:
        repo_name = info["repo_name"]
        repo_url = info["repo_url"]
        repo_owner = info["repo_owner"]
        repo_forks = info["forks_count"]
        repo_stars = info["stars_count"]
        repo_description = info["description"] if info["description"] != "" else "There is no description for this repo"
        repo_readme_content = info.get(
            "readme_content", "There is no README for this repo")

        summary = await summarize(lang, repo_readme_content, repo_description)

        results.append(
            {
                "name": repo_name,
                "owner": repo_owner,
                "version_control": "gitflame",
                "url": repo_url,
                "forks": repo_forks,
                "stars": repo_stars,
                "description": repo_description,
                "readme_content": repo_readme_content,
                "summary": summary,
            }
        )