from qa.utils.summarize import summarize
import httpx
import asyncio
import threading
import urllib


class GithubAPI():

    def __init__(self, access_token: str) -> None:
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {access_token}",
        }

    async def process_result(self, result: dict, results: list, lang: str = "en") -> None:
        repo_name = result["name"]
        repo_url = result["html_url"]
        repo_forks = result["forks_count"]
        repo_stars = result["stargazers_count"]
        repo_description = result["description"]
        repo_readme_content = await self.get_readme_content(result["full_name"])
        if repo_readme_content == "README not found or access denied.":
            repo_readme_content = "There is no README for this repo"

        # TODO
        summary = await summarize(lang, repo_readme_content, repo_description)

        results.append(
            {
                "name": repo_name,
                "version_control": "github",
                "url": repo_url,
                "forks": repo_forks,
                "stars": repo_stars,
                "description": repo_description,
                "readme_content": repo_readme_content,
                "summary": summary,
            }
        )


    async def search_repositories(self, query, repos: list, lang: str = "en"):

        print(query)

        url = "https://api.github.com/search/repositories"
        stars = "100"
        license = "mit"
        forks = "100"

        per_page = 5

        payload = {}
        
        params = {
            "q": query,
            # "stars": stars,
            # "license": license,
            # "forks": forks,
            "per_page": per_page,
            "page": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=self.headers, params=params)
                data = response.json()

            repositories = []
            threads = []

            for item in data.get("items", []):
                _t = threading.Thread(
                    target=asyncio.run,
                    args=(self.process_result(item, repositories, lang),),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()

            repos.extend(repositories)
        except Exception as e:
            print("Error occurred:", e)


    async def get_readme_content(self, full_name):
        url = f"https://api.github.com/repos/{full_name}/readme"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.text
        else:
            return "README not found or access denied."


    async def get_repo_info(self, repo_url: str) -> dict:
        # extract the owner and repo name
        url = urllib.parse.urlparse(repo_url)
        path = url.path.split("/")
        owner = path[1]
        repo = path[2]
        # construct the API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        # make the request
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(api_url)
            data = response.json()
        return data
