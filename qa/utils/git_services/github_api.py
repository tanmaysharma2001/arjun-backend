from qa.utils.summarize import summarize
import threading
from dotenv import load_dotenv, find_dotenv
import os
from base64 import b64decode
import requests

from utils.logger import logger


class GithubAPI:
    """A class to interact with the GitHub API for retrieving repository data."""

    def __init__(self, model: str = "openai") -> None:
        """Initialize the API client with authorization and model settings."""
        load_dotenv(find_dotenv())
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {os.environ['GITHUB_ACCESS_TOKEN']}"
        }
        self.model = model

    def process_result(self, result: dict, results: list, lang: str = "en") -> None:
        """Process each result and gather detailed information about the repository."""
        full_name = result["full_name"]
        repo_name = result["name"]
        repo_url = result["html_url"]
        repo_forks = result["forks_count"]
        repo_stars = result["stargazers_count"]
        repo_description = result["description"]
        repo_license = result.get("license", "No license info")

        # Gather additional information such as languages used, contributors, and README content
        languages = self.get_languages(full_name)
        contributors = self.get_contributors(full_name)
        repo_readme_content = self.get_readme_content(full_name)
        repo_readme_content = repo_readme_content if repo_readme_content != "README not found or access denied." else "There is no README for this repo"

        # Generate a summary of the repository content
        summary = summarize(lang, repo_readme_content, repo_description, model=self.model)

        results.append({
            "name": repo_name,
            "version_control": "github",
            "url": repo_url,
            "forks": repo_forks,
            "stars": repo_stars,
            "description": repo_description,
            "readme_content": repo_readme_content,
            "license": repo_license,
            "contributors": contributors,
            "languages": languages,
            "summary": summary,
        })

    def search_repositories(self, query, repos: list, lang: str = "en"):
        """Search repositories using GitHub API based on the given query."""
        search_url = "https://api.github.com/search/repositories"

        params = {
            "q": query,
            # "stars": stars,
            # "license": license,
            # "forks": forks,
            "per_page": 5,
            "page": 1,
        }

        try:
            response = requests.get(search_url, headers=self.headers, params=params)
            data = response.json()

            threads = []
            for repo_info in data.get("items", []):
                _t = threading.Thread(
                    target=self.process_result,
                    args=(repo_info, repos, lang),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()
        except Exception as e:
            logger.debug(f"Error occurred: {e}")

    def get_readme_content(self, full_name):
        """Retrieve the README content for a given repository."""
        try:
            url = f"https://api.github.com/repos/{full_name}/readme"
            response =  requests.get(url, headers=self.headers)
            if response.status_code == 200:
                readme = response.json()
                readme_content_decoded = b64decode(readme['content'])
                return readme_content_decoded
            else:
                return "README not found or access denied."
        except Exception as e:
            logger.debug(e)

    def get_contributors(self, full_name):
        """Fetch the list of contributors for a given repository."""
        try:
            url = f"https://api.github.com/repos/{full_name}/contributors"
            response = requests.get(url, headers=self.headers)
            return [contributor["login"] for contributor in response.json()] if response.status_code == 200 else "Contributors not found or access denied."
        except Exception as e:
            logger.debug(e)

    def get_languages(self, full_name):
        """Retrieve and calculate the percentage of languages used in a repository."""
        try:
            url = f"https://api.github.com/repos/{full_name}/languages"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                languages_data = response.json()
                total_bytes = sum(languages_data.values())
                return {lang: f"{(bytes / total_bytes) * 100:.2f}%" for lang, bytes in languages_data.items()}
            else:
                return "Languages for this repo were not found or access denied."
        except Exception as e:
            logger.debug(e)
