from typing import List
import requests

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

GIT_TOKEN = os.environ["GIT_TOKEN"]

from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries


def smart_search(lang, query):
    queries = generate_queries(lang, query)
    keywords = generate_keywords(lang, queries)
    repositories = []
    for keyword in keywords:
        repos = search_github_repositories(keyword)
        repositories.extend(repos)

    for repository in repositories:
        repository["metadata"] = (
            get_readme_content(repository["full_name"])
            if get_readme_content(repository["full_name"])
            != "README not found or access denied."
            else repository["description"]
        )
    return repositories


def search_github_repositories(query):

    print(query)

    url = "https://api.github.com/search/repositories"
    stars = "100"
    license = "mit"
    forks = "100"

    per_page = 10

    payload = {}
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GIT_TOKEN}",
    }

    params = {
        "q": query,
        "stars": stars,
        "license": license,
        "forks": forks,
        "per_page": per_page,
    }

    try:
        response = requests.request(
            "GET", url, headers=headers, data=payload, params=params
        )
        data = response.json()

        repositories = []

        for item in data.get("items", []):
            repo_name = item.get("name")
            repo_url = item.get("html_url")
            repo_forks = item.get("forks_count")
            repo_stars = item.get("stargazers_count")
            repo_full_name = item.get("full_name")
            repo_description = item.get("description")
            repositories.append(
                {
                    "name": repo_name,
                    "full_name": repo_full_name,
                    "url": repo_url,
                    "forks": repo_forks,
                    "stars": repo_stars,
                    "description": repo_description,
                }
            )

        return repositories
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
        return []


def get_readme_content(full_name):
    print(full_name)
    url = f"https://api.github.com/repos/{full_name}/readme"
    github_token = "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"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",
        "Authorization": f"token {github_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return "README not found or access denied."
