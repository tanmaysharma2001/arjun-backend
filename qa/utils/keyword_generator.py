import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import KEYWORD_GENERATOR_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]



async def generate_keywords(lang, queries):
    client = AsyncOpenAI(timeout=10)
    
    keyword_list = []

    for query in queries:
            
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
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
    return keyword_list
