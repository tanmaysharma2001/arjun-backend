import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import KEYWORD_GENERATOR_PROMPT
import threading
import asyncio

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

async def generate_keyword(client, model_name, lang, query, keyword_list):
    response = await client.chat.completions.create(
        model=model_name,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": KEYWORD_GENERATOR_PROMPT,
            },
            {
                "role": "user",
                "content": f"language: {lang} , query {query}",
            },
        ],
    )
    
    keywords = json.loads(response.choices[0].message.content)
    keyword_list.extend(keywords["keywords"])


async def generate_keywords(lang, queries, model):
    
    if model == "openai":
        client = AsyncOpenAI(timeout=10)
        model_name = "gpt-4-1106-preview"
    else:
        client = AsyncOpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        model_name = model

    keyword_list = []
    threads = []
    for query in queries:
        t = threading.Thread(
            target=asyncio.run,
            args=(generate_keyword(client, model_name, lang, query, keyword_list),)
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
        
    print(f"Keywords: {keyword_list}")
    return keyword_list
