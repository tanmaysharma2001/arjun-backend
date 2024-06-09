import asyncio
import threading

from bs4 import BeautifulSoup
import requests

class LaunchPadAPI():

    def __init__(self, model: str) -> None:
        self.model = model

    async def get_repo_info(self, repo_data, repositories):
        try:
            # Find the link in the first <a> tag within the row
            link = repo_data.find("a")["href"]
            # Find the name within the <a> tag
            name = repo_data.find("a").text.strip()
            # Find the description within the first <div> tag within the repo_data
            description = repo_data.find("div").find_next("div").text.strip()

            repo_url = "https://launchpad.net" + link
            licence_repo = ""
            languages_list = []
            contributors_list = []

            # Iterate over the repo link and find other information
            repo_response = requests.get(repo_url)
            repo_soup = BeautifulSoup(repo_response.content, "html.parser")

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
                "url": repo_url,
                "forks": 0,
                "stars": 0,
                "description": None,
                "readme_content": None,
                "summary": description,
                "licence": licence_repo,
                "languages": languages_list,
                "contributors": contributors_list
            }

            repositories.append(repo)
        except Exception as e:
            print("from get_repo_info_launchpad")
            print(e)

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
                    args=(self.get_repo_info(row, repositories),),
                    daemon=True
                )
                threads.append(_t)
                _t.start()

            # Wait for threads to finish
            for thread in threads:
                thread.join()

            results.extend(repositories)
        except Exception as e:
            print("from search_repo_launchpad")
            print(e)
