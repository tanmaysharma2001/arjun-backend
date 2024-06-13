import asyncio
import threading

from bs4 import BeautifulSoup
import requests

from utils.logger import logger


class LaunchPadAPI():

    def __init__(self, model: str) -> None:
        self.model = model

    def get_repo_info(self, url, lang: str = 'en'):

        summary = ""
        description = ""

        # Iterate over the repo link and find other information
        repo_response = requests.get(url)
        repo_soup = BeautifulSoup(repo_response.content, "html.parser")

        # get name and description
        name = repo_soup.find('h2', id="watermark-heading")

        if name:
            name = name.get_text(strip=True)

        # description is inside id = maincontent, inside class "yui-b"
        # inside "top-portlet", inside "description"
        div_maincontent = repo_soup.find('div', id="maincontent")
        div_yui_b = div_maincontent.find('div', {"class": "yui-b"})
        div_top_portlet = div_yui_b.find('div', {"class": "top-portlet"})
        div_summary_content = div_yui_b.find('div', {"class": "summary"})
        div_description_content = div_yui_b.find('div', {"class": "description"})

        if div_summary_content:
            summary = div_summary_content.get_text(strip=True)

        if div_description_content:
            description = div_description_content.get_text(strip=True)

        licence_repo = ""
        languages_list = []
        contributors_list = []

        # Find the License
        # Find the dl element with id "licences"
        licences_dl = repo_soup.find("dl", id="licences")

        # Check if the dl element was found
        if licences_dl:
            # Find the dd element within the dl element
            licence_dd = licences_dl.find("dd")

            # Check if the dd element was found and extract its text
            if licence_dd:
                licence_repo = licence_dd.get_text(strip=True)

        # Find the programming languages
        programming_lang_span = repo_soup.find("span", id="edit-programminglang")

        # Check if the span element was found and extract its text
        if programming_lang_span:
            programming_languages = programming_lang_span.get_text(strip=True)
            languages_list = programming_languages.split(",")
            languages_list = [lang.strip() for lang in languages_list]

        # Getting the contributors
        top_contributors_div = repo_soup.find("div", id="portlet-top-contributors")

        # Check if the div element was found
        if top_contributors_div:
            # Find all the a elements within the ul>li structure inside the div
            top_contributors_list = top_contributors_div.find_all("ul")
            hrefs = []
            for ul in top_contributors_list:
                a_tags = ul.find_all("a")
                hrefs.extend(["https://launchpad.net" + a['href'] for a in a_tags if 'href' in a.attrs])
            contributors_list = hrefs

        repo = {
            "name": name,
            "version_control": "launchpad",
            "url": url,
            "forks": 0,
            "stars": 0,
            "description": description,
            "readme_content": None,
            "summary": summary,
            "licence": licence_repo,
            "languages": languages_list,
            "contributors": contributors_list
        }

        return repo

    async def get_repo(self, repo_data, repositories):
        try:
            # Find the link in the first <a> tag within the row
            link = repo_data.find("a")["href"]

            # Find the name within the <a> tag
            # name = repo_data.find("a").text.strip()
            # # Find the description within the first <div> tag within the repo_data
            # description = repo_data.find("div").find_next("div").text.strip()

            repo_url = "https://launchpad.net" + link

            repo = self.get_repo_info(repo_url)

            repositories.append(repo)
        except Exception as e:
            logger.debug("from get_repo_info_launchpad")
            logger.debug(e)

    async def search_repositories(self, query, results: list, n_repos: int, lang: str = "en"):
        try:
            url = f"https://launchpad.net/projects?text=${query}&search=Find+a+Project"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the table with id "search-results"
            table = soup.find("table", {"id": "search-results"})

            if not table:
                return

            threads = []
            repositories = []
            # Iterate over each row in the table
            for i, row in enumerate(table.find_all("tr")):
                if i >= n_repos:
                    break

                _t = threading.Thread(
                    target=asyncio.run,
                    args=(self.get_repo(row, repositories),),
                    daemon=True
                )
                threads.append(_t)
                _t.start()

            # Wait for threads to finish
            for thread in threads:
                thread.join()

            results.extend(repositories)
        except Exception as e:
            logger.debug("from search_repo_launchpad")
            logger.debug(e)