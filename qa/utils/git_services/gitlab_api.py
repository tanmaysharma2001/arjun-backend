import gitlab
import threading
from qa.utils.summarize import summarize
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import os
import requests

from utils.logger import logger


class GitlabAPI():

    def __init__(self, model: str = "openai") -> None:
        load_dotenv(find_dotenv())
        self.gl = gitlab.Gitlab(
            'https://gitlab.com', private_token=os.environ["GITLAB_ACCESS_TOKEN"])
        self.model = model

    def get_repo_languages(self, project_id) -> dict:
        try:
            url = f"https://gitlab.com/api/v4/projects/{project_id}/languages"

            # Set up the headers with the access token
            headers = {
                "PRIVATE-TOKEN": os.environ["GITLAB_ACCESS_TOKEN"]
            }

            # Make the GET request to the URL
            response = requests.get(url, headers=headers)

            languages_list = response.json()

            return languages_list
        except Exception as e:
            logger.debug(e)

    def get_licence(self, id):
        try:
            url = f"https://gitlab.com/api/v4/projects/{id}?license=true"

            # Set up the headers with the access token
            headers = {
                "PRIVATE-TOKEN": os.environ["GITLAB_ACCESS_TOKEN"]
            }

            # Make the GET request to the URL
            response = requests.get(url, headers=headers)

            project = response.json()

            return project['license']
        except Exception as e:
            logger.debug(e)

    def get_repo_contributors(self, id):
        try:
            url = f"https://gitlab.com/api/v4/projects/{id}/repository/contributors"

            # Set up the headers with the access token
            headers = {
                "PRIVATE-TOKEN": os.environ["GITLAB_ACCESS_TOKEN"]
            }

            # Make the GET request to the URL
            response = requests.get(url, headers=headers)

            contributors_response = response.json()

            contributors = []

            for contributor in contributors_response:
                contributors.append(contributor['email'])

            return contributors
        except Exception as e:
            logger.debug(e)

    def process_result(self, project, results: list, lang: str = "en") -> None:
        try:
            project_name = project["name"]
            project_url = project["web_url"]
            project_forks = project["forks_count"]
            project_stars = project["star_count"]
            project_description = project["description"]

            # Project Languages
            languages = self.get_repo_languages(project["id"])

            # Get Licence
            project_license = self.get_licence(project["id"])

            if project_license:
                project_license = project_license['name']

            # Get contributors
            project_contributors = self.get_repo_contributors(project['id'])

            project_readme_content = self.get_readme_content(project["id"])
            if project_readme_content == "README not found or access denied.":
                project_readme_content = project_description

            # TODO
            summary = summarize(lang, project_readme_content, project_description, model=self.model)

            results.append({
                "name": project_name,
                "version_control": "gitlab",
                "url": project_url,
                "forks": project_forks,
                "stars": project_stars,
                "description": project_description,
                "license": project_license,
                "readme_content": project_readme_content,
                "summary": summary,
                "languages": languages,
                "contributors": project_contributors
            })
        except Exception as e:
            logger.debug(e)

    def search_repositories(self, query, repos: list, lang: str = "en"):
        try:
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
                    target=self.process_result,
                    args=(project, projects, lang),
                    daemon=True,
                )
                threads.append(_t)
                _t.start()
            for thread in threads:
                thread.join()

            repos.extend(projects)
        except Exception as e:
            logger.debug(e)

    def get_readme_content(self, project_id):
        try:
            project = self.gl.projects.get(project_id)
            readme = project.files.get(file_path='README.md', ref='master')
            return readme.decode()
        except Exception:
            logger.debug("README not found")
            return "README not found or access denied."

    def get_project_info(self, project_url: str) -> dict:
        project_id = project_url.split('/')[-1]
        project = self.gl.projects.get(project_id)
        return project.attributes

    def get_lincense(self, repo_url: str) -> dict:
        try:
            if not repo_url.startswith("http"):
                repo_url = "https://" + repo_url
            print(repo_url)
            response = requests.get(repo_url)
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            val = soup.find('span', class_='project-stat-value')
            # print(val.text)
            if val:
                return val.text
            return None

        except Exception as e:
            logger.debug(e)


    def get_repo_info(self, repo_url: str, lang="en"):
        project_path = repo_url.split(
            'gitlab.com/')[1] if 'gitlab.com/' in repo_url else repo_url

        try:
            project = self.gl.projects.get(project_path)

            # async with httpx.AsyncClient(timeout=10) as client:
            #     response = await client.get(project.members)
            #     print(response.json())

            repo_description = project.description
            readme_content = self.get_readme_content(project.id)
            if readme_content == "README not found or access denied.":
                readme_content = repo_description

            summary = summarize(
                lang=lang,
                readme_content=readme_content,
                description=repo_description,
                model=self.model
            )

            # Project ID
            project_id = project.id
            print(project_id)

            # Get Language Info
            language_list = self.get_repo_languages(project.id)

            info = {
                'name': project.name,
                'version_control': 'gitlab',
                'url': repo_url,
                'stars': project.star_count,
                'forks': project.forks_count,
                'summary': summary,
                'contributors': [project.namespace['name']],
                'licence': self.get_lincense(repo_url),
                "languages": language_list,
            }

            return info

        except Exception as e:
            logger.debug("Error while fetching gitlab repo info: ", e)
            return str(e)

