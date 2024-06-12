from qa.utils.git_services.gitflic_api import GitflicAPI
from qa.utils.git_services.github_api import GithubAPI
from qa.utils.git_services.gitverse_api import GitverseAPI
from qa.utils.git_services.gitlab_api import GitlabAPI
from qa.utils.git_services.launchpad_api import LaunchPadAPI
from qa.utils.git_services.moshub_api import MoshubAPI
from qa.utils.git_services.gitflame_api import GitFlameAPI
from qa.utils.git_services.gitee_api import GiteeAPI
from qa.utils.keyword_generator import generate_keywords
from qa.utils.query_generator import generate_queries
from qa.utils.summarize import get_final_summary
from qa.utils.rank import rank_repositories
import asyncio
import threading
import math


async def smart_search(lang, query, n_results, model):
    github_api = GithubAPI(model=model)
    gitverse_api = GitverseAPI(model=model)
    gitlab_api = GitlabAPI(model=model)
    moshub_api = MoshubAPI(model=model)
    gitflame_api = GitFlameAPI(model=model)
    launchpad_api = LaunchPadAPI(model=model)
    gitee_api = GiteeAPI(model=model)
    gitflic_api = GitflicAPI(model = model)

    en_queries = await generate_queries("en", query, model=model)
    en_queries = en_queries[:2]
    en_keywords = await generate_keywords("en", en_queries, model=model)
    en_keywords = en_keywords[:4]

    ru_queries = await generate_queries("ru", query, model=model)
    ru_queries = ru_queries[:2]

    ru_keywords = await generate_keywords("ru", ru_queries, model=model)
    ru_keywords = ru_keywords[:4]

    if en_queries and ru_queries and en_keywords and ru_keywords:
        print("Successfully generated queries & keywords")

    github_repositories = []
    gitverse_repositories = []
    gitlab_repositories = []
    moshub_repositories = []
    gitflame_repositories = []
    launchpad_repositories = []
    gitee_repositories = []

    threads = []

    # Searching through each Git Providers
    for i in range(min(len(en_keywords), len(ru_keywords))):

        # Github
        _t = threading.Thread(
            target=asyncio.run,
            # Search in english only because github api doesn't provide good results for russian keywords
            args=(
                github_api.search_repositories(
                    en_keywords[i], github_repositories, lang
                ),
            ),
            daemon=True,
        )
        threads.append(_t)
        _t.start()

        # # Gitverse
        # _t = threading.Thread(
        #     target=asyncio.run,
        #     args=(
        #         gitverse_api.search_repositories(
        #             query=ru_keywords[i],
        #             repos=gitverse_repositories,
        #             lang="ru"
        #         ),
        #     ),
        #     daemon=True
        # )
        # threads.append(_t)
        # _t.start()

        # Gitlab
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitlab_api.search_repositories(
                    query=en_keywords[i] if lang == "en" else ru_keywords[i],
                    repos=gitlab_repositories,
                    lang=lang,
                ),
            ),
            daemon=True,
        )

        threads.append(_t)
        _t.start()

        # Moshub
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                moshub_api.search_repositories(
                    query=ru_keywords[i],
                    repos=moshub_repositories,
                    n_repos=5,
                    lang=lang,
                ),
            ),
            daemon=True,
        )

        threads.append(_t)
        _t.start()

        # Gitflame
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitflame_api.search_repositories(
                    query=ru_keywords[i],
                    results=gitflame_repositories,
                    n_repos=5,
                    lang=lang,
                ),
            ),
            daemon=True,
        )

        threads.append(_t)
        _t.start()

        # LaunchPad
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                launchpad_api.search_repositories(
                    query=en_keywords[i],
                    results=launchpad_repositories,
                    n_repos=5,
                    lang=lang,
                ),
            ),
        )

        threads.append(_t)
        _t.start()

        # Gitee
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitee_api.search_repositories(
                    query=en_keywords[i] if lang == "en" else ru_keywords[i],
                    repos=gitlab_repositories,
                    lang=lang,
                    n_repos=1,
                ),
            ),
        )

        threads.append(_t)
        _t.start()

        # Gitflic
        _t = threading.Thread(
            target=asyncio.run,
            args=(
                gitflic_api.search_repositories(
                    query=en_keywords[i],
                    repos=gitflic_repositories,
                    lang=lang,
                ),
            ),
        )

        threads.append(_t)
        _t.start()

    for thread in threads:
        thread.join()

    # readme_content and description are not necessary anymore
    for repo in github_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    # for repo in gitverse_repositories:
    #     repo.pop("readme_content", None)
    #     repo.pop("description", None)

    for repo in gitlab_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in moshub_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in gitflame_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in launchpad_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    for repo in gitee_repositories:
        repo.pop("readme_content", None)
        repo.pop("description", None)

    # get only the unique repositories from each version control, rank them and get the top repos
    no_match_str = "Didn't find any matching repo for this query on "
    final_result = []

    if github_repositories:
        github_repositories = get_unique_repos(github_repositories)
        print(
            f"Ranking {len(github_repositories)} Github repositories based on their summaries..."
        )
        ranked_github_repositories = rank_repositories(
            query, github_repositories, math.floor(n_results * 0.4)
        )
        final_result.append(ranked_github_repositories)
    else:
        print(no_match_str + "Github")

    # if gitverse_repositories:
    #     gitverse_repositories = get_unique_repos(gitverse_repositories)
    #     print(f"Ranking {len(gitverse_repositories) } Gitverse repositories based on their summaries...")
    #     ranked_gitverse_repositories = rank_repositories(
    #         query, gitverse_repositories, math.floor(n_results * 0.2))
    #     final_result.append(ranked_gitverse_repositories)
    # else:
    #     print(no_match_str + "Gitverse")

    if gitlab_repositories:
        gitlab_repositories = get_unique_repos(gitlab_repositories)
        print(
            f"Ranking {len(gitlab_repositories) } Gitlab repositories based on their summaries..."
        )
        ranked_gitlab_repositories = rank_repositories(
            query, gitlab_repositories, math.floor(n_results * 0.2)
        )
        final_result.append(ranked_gitlab_repositories)
    else:
        print(no_match_str + "Gitlab")

    if launchpad_repositories:
        launchpad_repositories = get_unique_repos(launchpad_repositories)
        print(
            f"Ranking {len(launchpad_repositories) } Launchpad repositories based on their summaries..."
        )
        ranked_launchpad_repositories = rank_repositories(
            query, launchpad_repositories, math.floor(n_results * 0.2)
        )
        final_result.append(ranked_launchpad_repositories)
    else:
        print(no_match_str + "LaunchPad")

    if moshub_repositories:
        moshub_repositories = get_unique_repos(moshub_repositories)
        print(
            f"Ranking {len(moshub_repositories)} Moshub repositories based on their summaries..."
        )
        ranked_moshub_repositories = rank_repositories(
            query, moshub_repositories, math.floor(n_results * 0.1)
        )
        final_result.append(ranked_moshub_repositories)
    else:
        print(no_match_str + "Moshub")

    if gitflame_repositories:
        gitflame_repositories = get_unique_repos(gitflame_repositories)
        print(
            f"Ranking {len(gitflame_repositories)} Gitflame repositories based on their summaries..."
        )
        ranked_gitflame_repositories = rank_repositories(
            query, gitflame_repositories, math.floor(n_results * 0.1)
        )
        final_result.append(ranked_gitflame_repositories)
    else:
        print(no_match_str + "Gitflame")

    if gitee_repositories:
        gitee_repositories = get_unique_repos(gitee_repositories)
        print(
            f"Ranking {len(gitee_repositories)} Gitee repositories based on their summaries..."
        )
        ranked_gitee_repositories = rank_repositories(
            query, gitee_repositories, math.floor(n_results * 0.1)
        )
        final_result.append(ranked_gitee_repositories)
    else:
        print(no_match_str + "Gitee")

    
    if gitflic_repositories:
        gitflic_repositories = get_unique_repos(gitflic_repositories)
        print(
            f"Ranking {len(gitflic_repositories)} GitFlic repositories based on their summaries..."
        )
        ranked_gitflic_repositories = rank_repositories(
            query, gitflic_repositories, math.floor(n_results * 0.1)
        )
        final_result.append(ranked_gitflic_repositories)
    else:
        print(no_match_str + "Gitflic")

    if final_result:
        final_result = final_result[:10]
        summary = await get_final_summary(
            ranked_repositories=final_result, model=model
        )

        return {"summary": summary, "sources": final_result}

    else:
        return {"summary": "No results found", "sources": []}


def get_unique_repos(repositories: list):
    done = set()
    result = []
    for repo in repositories:
        try:
            if repo["url"] not in done:
                done.add(repo["url"])
                result.append(repo)
        except Exception as e:
            print("Error at repo:")
            print(repo)
            print(e)
    return result
