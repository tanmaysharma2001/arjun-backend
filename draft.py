import requests
from bs4 import BeautifulSoup


def scrape_gitverse(gitverse_repo_url: str) -> dict:
    info = {}

    print(f"Scraping {gitverse_repo_url}")

    html_content = requests.get(gitverse_repo_url).text

    soup = BeautifulSoup(html_content, 'html.parser')

    # Get title
    info['title'] = soup.findAll('h1')[0].text

    # Get forks
    forks_element = soup.find_all(string="Форк")[0].find_next_sibling("div")
    info['forks'] = int(forks_element.text.strip())

    # Get stars
    for span in soup.find_all('span'):
        if span.text == " В избранное":
            stars = int(span.find_next_sibling("div").text)

    info['stars'] = stars

    info['readme_content'] = get_readme_content_gitverse(gitverse_repo_url)

    return info


def get_readme_content_gitverse(gitverse_repo_url: str) -> str:
    gitverse_repo_full_name = gitverse_repo_url.split(
        "/")[3] + "/" + gitverse_repo_url.split("/")[4]
    readme_content = "no readme"
    possible_branch_names = ["master", "main"]
    md_variations = ["md", "MD"]
    for branch in possible_branch_names:
        for md_variation in md_variations:
            gitverse_repo_readme_url = \
                f"https://gitverse.ru/api/repos/{gitverse_repo_full_name}/raw/branch/{branch}/README.{md_variation}"
            response = requests.get(gitverse_repo_readme_url)
            if response.status_code == 400:
                continue
            readme_content = response.text

    return readme_content


print(scrape_gitverse("https://gitverse.ru/githubmirror/free-for-dev")['forks'])
