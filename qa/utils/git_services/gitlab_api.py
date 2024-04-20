import gitlab
import asyncio
import threading
from qa.utils.summarize import summarize


class GitlabAPI():

    def __init__(self, token: str) -> None:
        self.token = token
        self.gl = gitlab.Gitlab('https://gitlab.com', private_token=self.token)

    async def process_result(self, project, results: list, lang: str = "en") -> None:
        project_name = project["name"]
        project_url = project["web_url"]
        project_forks = project["forks_count"]
        project_stars = project["star_count"]
        project_description = project["description"]
        project_readme_content = await self.get_readme_content(project["id"])
        if project_readme_content == "README not found or access denied.":
            project_readme_content = project_description

        # TODO
        summary = await summarize(lang, project_readme_content, project_description)

        results.append({
            "name": project_name,
            "version_control": "gitlab",
            "url": project_url,
            "forks": project_forks,
            "stars": project_stars,
            "description": project_description,
            "readme_content": project_readme_content,
            "summary": summary,
        })

    async def search_repositories(self, query, repos: list, lang: str = "en"):
        per_page = 5
        page = 1
        search_results = self.gl.search(
            scope=gitlab.const.SearchScope.PROJECTS,
            search=query, 
            page=page, 
            per_page=per_page)

        threads = []
        projects = []
        for project in search_results:
            _t = threading.Thread(
                target=asyncio.run,
                args=(self.process_result(project, projects, lang),),
                daemon=True,
            )
            threads.append(_t)
            _t.start()
        for thread in threads:
            thread.join()

        repos.extend(projects)

    async def get_readme_content(self, project_id):
        try:
            project = self.gl.projects.get(project_id)
            readme = project.files.get(file_path='README.md', ref='master')
            return readme.decode()
        except Exception:
            return "README not found or access denied."

    async def get_project_info(self, project_url: str) -> dict:
        project_id = project_url.split('/')[-1]
        project = self.gl.projects.get(project_id)
        return project.attributes
