import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import asyncio


class GiteeAPI:
    def __init__(self, model="openai"):
        self.model = model
        self.driver = self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    async def fetch_repo_details(self, repo_url):
        self.driver.get(repo_url)
        await asyncio.sleep(10)
        readme_content = "No README found."
        languages = []
        stars = 0
        forks = 0

        if self.model == "openai":
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "git-readme"))
                )
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, features="html.parser")
                readme_box = soup.find("div", id="git-readme")
                if readme_box:
                    readme_content = readme_box.get_text(strip=True)
            except Exception as e:
                print("Error fetching README:", e)

        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, features="html.parser")
            language_rows = soup.find_all("div", class_="row")
            for row in language_rows:
                lang_elem = row.find("div", class_="lang")
                if lang_elem:
                    lang_name = lang_elem.get_text(strip=True)
                    lang_percentage_elem = row.find("a", class_="percentage")
                    lang_percentage = (
                        lang_percentage_elem.get_text(strip=True)
                        if lang_percentage_elem
                        else "0%"
                    )
                    languages.append(
                        {"language": lang_name, "percentage": lang_percentage}
                    )
        except Exception as e:
            print("Error fetching languages:", e)

        try:
            stars_elem = soup.find("span", class_="repo-stars")
            forks_elem = soup.find("span", class_="repo-forks")
            if stars_elem:
                stars = int(stars_elem.get_text(strip=True).replace(",", ""))
            if forks_elem:
                forks = int(forks_elem.get_text(strip=True).replace(",", ""))
        except Exception as e:
            print("Error fetching stars and forks:", e)

        return readme_content, languages, stars, forks

    async def search_repositories(
        self, query, repos: list, lang: str = "en", n_repos: int = 2
    ):
        page = 1
        url = f"https://so.gitee.com/?q={query}&page={page}"
        self.driver.get(url)
        await asyncio.sleep(10)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, features="html.parser")

        cards = soup.find_all("div", class_="card border-1 mb-3")
        for i, card in enumerate(cards):
            if i >= n_repos:
                break
            title_link = card.find("h4", class_="card-title").find(
                "a", class_="title"
            )
            name = title_link.text.strip()
            link = title_link["href"]
            description = card.find(
                "div", class_="col-12 outline text-secondary"
            ).text.strip()

            readme_content, languages, stars, forks = (
                await self.fetch_repo_details(link)
            )

            repos.append(
                {
                    "name": name,
                    "version_control": "gitee",
                    "url": link,
                    "forks": forks,
                    "stars": stars,
                    "description": description,
                    "readme_content": readme_content,
                    "languages": languages,
                    "summary": description,
                }
            )

    async def get_repo_info(self, repo_url: str, lang: str) -> dict:
        repo_name = repo_url.split("/")[4]
        repo_owner = repo_url.split("/")[3]
        readme_content, languages, stars, forks = (
            await self.fetch_repo_details(repo_url)
        )

        summary = ""

        info = {
            "name": repo_name,
            "version_control": "gitee",
            "url": repo_url,
            "contributors": [repo_owner],
            "forks": forks,
            "stars": stars,
            "summary": summary,
            "languages": languages,
            "licence": "",
        }

        return info

    def close(self):
        self.driver.quit()


# async def main():
#     api = GiteeAPI()  # Use "openai" to fetch README content

#     repo_info = await api.get_repo_info("https://gitee.com/fasiondog/hikyuu", "en")
#     print("Specific Repository Info:", repo_info)

#     repositories = []
#     await api.search_repositories("c++", repositories, n_repos=2)
#     for repo in repositories:
#         print("Repository Info:", repo)

#     api.close()

# if __name__ == "__main__":
#     asyncio.run(main())
