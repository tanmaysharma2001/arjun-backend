import httpx
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()
GIT_TOKEN = os.getenv("GIT_TOKEN")

async def get_readme_content_github(full_name):
    print(full_name)
    url = f"https://api.github.com/repos/{full_name}"
    headers = {
        "Accept": "application/vnd.github.v3.raw+json",
        "Authorization": f"token {GIT_TOKEN}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    print(response.json())
    
# run the code
full_name = "pptx704/domainim"
content = asyncio.run(get_readme_content_github(full_name))