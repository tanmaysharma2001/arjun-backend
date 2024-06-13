import threading
import typing
import requests

from qa.utils.summarize import summarize
from utils.logger import logger


class GitFlameAPI():
    def __init__(self, model: str = "openai"):
        self.api_url = "https://gitflame.ru/api/v1/repos"
        self.model = model

    def search_repositories(self, query: str, results: list, n_repos: int, lang: str = "ru") -> list:
        try:
            repositories = requests.get(
                url=self.get_search_url(),
                params={
                    "page": 1,
                    "limit": n_repos,
                    "q": query,
                    "is_private": False,
                })

            search_results = []
            threads = []

            for repo_data in repositories.json():
                _t = threading.Thread(
                    target=self.process_result,
                    args=(
                        repo_data, search_results, lang
                    ),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()

            results.extend(search_results)

        except Exception as e:
            logger.debug(f"An error occurred: {e}")
            return []

    def get_search_url(self) -> str:
        return self.api_url + "/search"

    def get_readme_urls(self, owner: str, repo_name: str) -> typing.List[str]:
        prefix = f"{self.api_url}/{owner}/{repo_name}/raw//"
        return [
            prefix + "README.md",
            prefix + "readme.md",
            prefix + "ReadMe.md",
        ]

    def get_readme_content(self, readme_url: str) -> str:
        readme = requests.get(
            url=readme_url)
        if readme.status_code == 200 and not readme.content.decode().startswith("<!DOCTYPE html>"):
            return readme.content.decode()
        logger.debug("Can not find readme.md for gitflame for this link: ",
                     readme_url)
        return ""

    def get_languages(self, languages_url: str):

        response = requests.get(languages_url)
        if response.status_code == 200:
            languages_data = response.json()
            total_bytes = sum(languages_data.values())
            return {lang: f"{(bytes / total_bytes) * 100:.2f}%" for lang, bytes in languages_data.items()}
        else:
            return "Languages for this repo were not found or access denied."

    # This function is never called, as gitflame requires authentaction
    # to access the collaborators api endpoint, and I couldn't find a way to
    # do the authentication as gitflame doesn't support api keys
    def get_contributors(self, repo_fullname: str):
        contributors_url = f"{self.api_url}/{repo_fullname}/collaborators"
        response = requests.get(contributors_url)
        print(response)
        return [contributor["login"] for contributor in
                response.json()] if response.status_code == 200 else "Contributors not found or access denied."

    def process_result(self, data: dict, results: list, lang: str = "en") -> None:
        # A repo's fullname is the name of the owner followed by a '/', then by repo's name
        repo_fullname = data["full_name"]

        repo_name = data["name"]
        repo_url = data["html_url"]
        repo_owner = data["owner"]["username"]
        repo_forks = data["forks_count"]
        repo_stars = data["stars_count"]
        repo_languages = self.get_languages(data["languages_url"])
        # repo_contributors = await self.get_contributors(repo_fullname)
        repo_contributors = "N/A"

        # GitFlame doesn't support adding a license to a repository, that's
        # why we're defaulting to "N/A" here.
        repo_license = "N/A"

        repo_description = data.get(
            "descriptoin", "There is no description for this repo")

        for possible_readme_url in self.get_readme_urls(owner=repo_owner, repo_name=repo_name):
            repo_readme_content = self.get_readme_content(possible_readme_url)
            if repo_readme_content != "":
                data["readme_content"] = repo_readme_content
                break

        repo_readme_content = data.get(
            "readme_content", "There is no README for this repo")

        summary = summarize(lang, repo_readme_content, repo_description, self.model)

        results.append(
            {
                "name": repo_name,
                "owner": repo_owner,
                "version_control": "gitflame",
                "url": repo_url,
                "forks": repo_forks,
                "stars": repo_stars,
                "license": repo_license,
                "languages": repo_languages,
                "contributors": repo_contributors,
                "description": repo_description,
                "readme_content": repo_readme_content,
                "summary": summary,
            }
        )

    def get_repo_info(self, repo_url: str, lang: str) -> dict:
        repo_name = repo_url.split("/")[4]
        repo_owner = repo_url.split("/")[3]
        repo_description = ""
        readme_content = ""
        for possible_readme_url in self.get_readme_urls(repo_name=repo_name, owner=repo_owner):
            repo_readme_content = self.get_readme_content(possible_readme_url)
            if repo_readme_content != "":
                readme_content = repo_readme_content
                break

        summary = summarize(lang, readme_content, repo_description, self.model)

        info = {
            "name": repo_name,
            "version_control": "gitflame",
            "url": repo_url,
            "contributors": [repo_owner],
            "forks": 0,
            "stars": 0,
            "summary": summary,
            "license": "N/A",
        }

        return info
