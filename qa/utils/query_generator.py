import os
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import QUERY_GENERATOR_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

def generate_queries(lang, query, model):
    if model == "openai":
        client = OpenAI(timeout=10)

        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
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
        print(f"Queries ({lang}): {queries}")
        return queries["queries"]
    else:

        client = OpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        print(model)

        response = client.chat.completions.create(
            model=model,
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