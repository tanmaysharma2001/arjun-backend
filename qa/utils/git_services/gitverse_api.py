from bs4 import BeautifulSoup
import httpx
import xmltodict
import asyncio
import threading
from qa.utils.summarize import summarize
from dotenv import load_dotenv, find_dotenv
import os
import requests

from utils.logger import logger


class GitverseAPI():
    def __init__(self, model:str = "openai"):
        load_dotenv(find_dotenv())
        self.yc_folder = os.getenv("YC_FOLDER")
        self.yc_secret_key = os.getenv("YC_SECRET")
        self.model = model


    def search_repositories(self, query: str, repos: list, lang: str = "en"):
        url = "https://yandex.ru/search/xml"
        params = {
            "folderid": self.yc_folder,
            "apikey": self.yc_secret_key,
        }
        results = []

        params["query"] = query + " host:gitverse.ru"
        response = requests.get(url, params=params)
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
                target=self.process_result,
                args=(result, results, lang),
                daemon=True,
            )
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()

        repos.extend(results)

    def scrape_info(self, gitverse_repo_url: str) -> dict:

        info = {}

        print(f"Scraping {gitverse_repo_url}")
        try:
            response = requests.get(gitverse_repo_url)
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            # Get name
            info["name"] = soup.findAll("h1")[0].text

            # Get forks
            forks_element = soup.find_all(string="Форк")[
                0].find_next_sibling("div")
            info["forks"] = int(forks_element.text.strip())

            # Get stars
            for span in soup.find_all("span"):
                if span.text == " В избранное":
                    stars = int(span.find_next_sibling("div").text)

            info["stars"] = stars

            info["readme_content"] = self.get_readme_content(gitverse_repo_url)
            info['license'] = ""
            info['contributors'] = [gitverse_repo_url.split('/')[3]]

            h4_tag = soup.find('h4', class_='text-h4')

            # Since the <p> tag follows <h4>, you can use .find_next() to get the next <p> tag
            if h4_tag:
                p_tag = h4_tag.find_next('p')
                if p_tag:
                    info["description"] = p_tag.text
                else:
                    info["description"] = ""
            else:
                info["description"] = ""

        except Exception as e:
            logger.debug(e)

        return info

    def get_readme_content(self, gitverse_repo_url: str) -> str:

        gitverse_repo_full_name = (
            gitverse_repo_url.split(
                "/")[3] + "/" + gitverse_repo_url.split("/")[4]
        )
        readme_content = "no readme"
        possible_branch_names = ["master", "main"]
        md_variations = ["md", "MD"]
        for branch in possible_branch_names:
            for md_variation in md_variations:
                gitverse_repo_readme_url = f"https://gitverse.ru/api/repos/{gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
                response = requests.get(gitverse_repo_readme_url)
                if response.status_code == 400:
                    continue
                readme_content = response.text

        return readme_content

    def extract_repo_url(self, file_url: str) -> str:
        # Split the URL into parts
        parts = file_url.split("/")
        # Check if the URL is valid and contains enough parts to extract the repo URL
        if len(parts) >= 5:
            # Reconstruct the repo URL
            repo_url = "/".join(parts[:5])
            return repo_url
        else:
            return None

    def process_result(
        self, yandex_search_result: dict, results: list, lang: str = "ru"
    ) -> None:
        repo_url = self.extract_repo_url(yandex_search_result["url"])

        if repo_url is not None:
            try:
                repo_info = self.scrape_info(repo_url)
                repo_name = repo_info["name"]
                forks = repo_info["forks"]
                stars = repo_info["stars"]
                readme_content = repo_info["readme_content"]
                description = yandex_search_result.get("headline")
                contributors = repo_info.get("contributors", [])
                summary = summarize(lang, readme_content, description, model=self.model)
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
                logger.debug(f"Error occurred while scraping {repo_url}. Details:", e)

    def get_repo_info(self, repo_url: str, lang: str) -> dict:
        data = self.scrape_info(repo_url)
        repo_license = data['license']
        repo_name = data["name"]
        repo_forks = data["forks"]
        repo_stars = data["stars"]
        repo_contributors = data['contributors']
        repo_description = data["description"]
        repo_readme_content = self.get_readme_content(repo_url)
        if repo_readme_content == "README not found or access denied.":
            repo_readme_content = "There is no README for this repo"

        summary = summarize(lang, repo_readme_content, repo_description, model=self.model)

        info = {
            "name": repo_name,
            "version_control": "gitverse",
            "url": repo_url,
            "forks": repo_forks,
            "stars": repo_stars,
            "licence": repo_license,
            "summary": summary,
            "contributors" : repo_contributors,
        }
        return info
