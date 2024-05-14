from bs4 import BeautifulSoup
import requests

class LaunchPadAPI():

    def __init__(self, model: str) -> None:
        self.model = model
    

    async def search_repositories(self, query, results: list, n_repos: int, lang: str = "en"):
        url = f"https://launchpad.net/projects?text=${query}&search=Find+a+Project"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table with id "search-results"
        table = soup.find("table", {"id": "search-results"})

        # Initialize lists to store data
        links = []
        names = []
        descriptions = []

        repositories = []

        # Iterate over each row in the table
        for row in table.find_all("tr"):
            # Find the link in the first <a> tag within the row
            link = row.find("a")["href"]
            # Find the name within the <a> tag
            name = row.find("a").text.strip()
            # Find the description within the first <div> tag within the row
            description = row.find("div").find_next("div").text.strip()

            # Append data to respective lists
            links.append(link)
            names.append(name)
            descriptions.append(description)

            repositories.append({
                "name": name,
                "version_control": "launchpad",
                "url": "https://launchpad.net" + link,
                "forks": 0,
                "stars": 0,
                "description": None,
                "readme_content": None,
                "summary": description
            })  

        results.extend(repositories)

