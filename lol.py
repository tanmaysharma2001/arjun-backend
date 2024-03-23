import requests

def get_readme_content(full_name):
    """
    Fetches the README content of the specified GitHub repository.

    Args:
    - full_name (str): The full name of the repository (e.g., "owner/repo").

    Returns:
    - str: The content of the README file, or an error message if the request fails.
    """
    url = f"https://api.github.com/repos/{full_name}/readme"
    github_token = "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"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",  # Get the raw README content
        # Optional: For higher rate limit and private repos
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text  # Raw README content
    else:
        return "README not found or access denied."
    
    
lol = get_readme_content("erenavsarogullari/OTV_Spring_Integration_Message_Processing")


lol
    
    