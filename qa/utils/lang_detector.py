import os
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

from utils.logger import logger
from .prompts import LANG_DETECTOR_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

def detect_lang(query, model):
    try:
        if model == "openai":

            client = OpenAI(timeout=30)

            response = client.chat.completions.create(
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
            client = OpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
            print(model)
            response = client.chat.completions.create(
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

    except Exception as e:
        logger.debug(e)
        return {
            "detected_language": "en",
            "confidence_score": 0.98
        }

