import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import LANG_DETECTOR_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

async def detect_lang(query, model):
    if model == "openai":

        client = AsyncOpenAI(timeout=10)

        response = await client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": LANG_DETECTOR_PROMPT,
                },
                {"role": "user", "content": json.dumps({"text_query": query})},
            ],
        )
        print(response.choices[0].message.content)
        return json.loads(response.choices[0].message.content)

    else: 
        client = AsyncOpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        print(model)
        response = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": LANG_DETECTOR_PROMPT,
                },
                {"role": "user", "content": json.dumps({"text_query": query})},
            ],
        )
        print(response.choices[0].message.content)
        return json.loads(response.choices[0].message.content)

