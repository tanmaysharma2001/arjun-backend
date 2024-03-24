import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import QUERY_GENERATOR_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

async def generate_queries(lang, query):
    client = AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": QUERY_GENERATOR_PROMPT,
            },
            {
                "role": "user",
                "content": f"language: {lang} , query {query}",
            },
        ],
    )

    queries = json.loads(response.choices[0].message.content)
    print(queries)
    return queries["queries"]
