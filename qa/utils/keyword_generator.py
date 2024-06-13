import os
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import KEYWORD_GENERATOR_PROMPT
import threading

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

def generate_keyword(client, model_name, lang, query, keyword_list):
    response = client.chat.completions.create(
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


def generate_keywords(lang, queries, model):
    print(f"Generating keywords for ({lang})")

    if model == "openai":
        client = OpenAI(timeout=10)
        model_name = "gpt-4-1106-preview"
    else:
        client = OpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        model_name = model

    keyword_list = []
    threads = []
    for query in queries:
        t = threading.Thread(
            target=generate_keyword,
            args=(client, model_name, lang, query, keyword_list)
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
        
    print(f"Keywords ({lang}): {keyword_list}")
    return keyword_list
