from typing import Union
from typing import List, Dict

import httpx
from fastapi import FastAPI, HTTPException

import serpapi


API_KEY = "d4ef59d3ff953eae8e1187af50632f2069f72bd86733fc91f6db75dd86e626a1"


app = FastAPI()

# Async function to fetch search results from an example API
async def fetch_search_results(engine: str, query: str, search_language: str) -> List[Dict]:

    params = {
        "q": query,
        "engine": engine,
        "api_key": API_KEY,
    }

    # Perform the asynchronous HTTP GET request
    async with httpx.AsyncClient() as client:
        response = serpapi.search(params)

        print(response)

        # Parse the response as JSON
        data = response.as_dict()

        organic_results = data['organic_results']
    
    print(organic_results)

    return organic_results


@app.get("/search/")
async def search(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Language Detection
    # If English then Google then Yandex
    # If russian then google (lanugage russian and country russia) and then yandex

    # If google search using keywords before github:, gitlab:, gitverse:, moscowhub:
    # If russian then keywords before gitverse:, moscowhub:, github:, gitlab:

    search_language = "ru"
    query = "site:github.com Open Source Financial Application"
    
    # Fetch results asynchronously from various search engines
    google_results = await fetch_search_results("Google", query, search_language)
    # duckduckgo_results = await fetch_search_results("DuckDuckGo", query, search_language)
    
    return {
        "Google": google_results,
        # "DuckDuckGo": duckduckgo_results,
    }

@app.get("/")
def read_root():
    return {"Hello": "World"}