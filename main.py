from typing import List, Dict
import httpx
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import serpapi
import os
import xmltodict

load_dotenv()

class SearchResult:
    def __init__(self, version_control, link, description):
        self.version_control = version_control
        self.link = link
        self.description = description

VERSION_CONTROLS = [
    'github.com',
    'gitlab.com',
    'hub.mos.ru',
    'gitverse.ru'
]

SEARCH_ENGINES = [
    # 'google',
    # 'duckduckgo',
    'yandex'
]

API_KEY = os.getenv("SERP_API")
YC_FOLDER = os.getenv("YC_FOLDER")
YC_SECRET_KEY = os.getenv("YC_SECRET")


app = FastAPI()

async def yandex_search(query: str):
    url = "https://yandex.ru/search/xml"
    params = {
        "folderid": YC_FOLDER,
        "apikey": YC_SECRET_KEY,
    }
    results = []
    async with httpx.AsyncClient() as client:
        for vc in VERSION_CONTROLS:
            params["query"] = query + " host:" + vc
            response = await client.get(url, params=params)
            data_dict = xmltodict.parse(response.text)
            try:
                _res = data_dict["yandexsearch"]["response"]["results"]["grouping"]["group"]
            except KeyError:
                print(data_dict)
                _res = []
            for result in _res:
                doc = result["doc"]
                results.append({
                    "url": doc["url"],
                    "title": doc["title"],
                    "headline": doc.get("headline"),
                })
        
    return results

# Async function to fetch search results from an example API
async def fetch_search_results(engine: str, query: str, search_language: str) -> List[Dict]:
    if engine.lower() == "yandex":
        return await yandex_search(query)
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
        

        organic_results = data.get('organic_results')
    

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

    search_language = "ru" # Call the language detection service here
    RESULTS = {}    
    for engine in SEARCH_ENGINES:
        engine_results = {}
        result = await fetch_search_results(engine = engine, query= query, search_language=search_language)
        RESULTS[engine] = result

    return RESULTS

@app.get("/")
def read_root():
    return {"Hello": "World"}