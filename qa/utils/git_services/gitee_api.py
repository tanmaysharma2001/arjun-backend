from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import asyncio


class GiteeAPI:
    def __init__(self, model: str, driver):
        self.model = model
        self.driver = driver

    def fetch_readme_content(self, repo_url):
        if self.model == "openai":
            self.driver.get(repo_url)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "git-readme"))
                )
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                readme_box = soup.find("div", id="git-readme")
                if readme_box:
                    return readme_box.get_text(strip=True)
            except Exception as e:
                print("Error fetching README:", e)
            return "No README found."
        else:
            return None

    def search_repositories(self, query, repos: list, page: int = 1):
        url = f"https://so.gitee.com/?q={query}&page={page}"
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-body"))
        )
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        cards = soup.find_all("div", class_="card border-1 mb-3")
        for card in cards:
            title_link = card.find("h4", class_="card-title").find(
                "a", class_="title"
            )
            name = title_link.text.strip()
            link = title_link["href"]
            description = card.find(
                "div", class_="col-12 outline text-secondary"
            ).text.strip()
            readme_url = link

            readme_content = self.fetch_readme_content(readme_url)

            metadata = card.find(
                "div", class_="col-12 text-muted mt-2 metadata"
            )
            stars = (
                metadata.find_all("span")[1].text
                if len(metadata.find_all("span")) > 1
                else "0"
            )
            forks = (
                metadata.find_all("span")[2].text
                if len(metadata.find_all("span")) > 2
                else "0"
            )

            repos.append(
                {
                    "name": name,
                    "version_control": "gitee",
                    "url": link,
                    "forks": int(forks),
                    "stars": int(stars),
                    "description": description,
                    "readme_content": readme_content,
                    "summary": description,
                }
            )


def setup_driver():
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


# async def main():
#     driver = setup_driver()
#     api = GiteeAPI("test-model", driver)
#     repositories = []
#     api.search_repositories("c++", repositories)
#     for repo in repositories:
#         print(repo)
#     driver.quit()

# if __name__ == "__main__":
#     asyncio.run(main())