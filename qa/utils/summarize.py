import os
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

from utils.logger import logger
from .prompts import MASTER_SUMMERIZER_PROMPT, SUMMERIZER_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]


def summarize(lang, readme_content, description, model):
    try:
        if model == "openai":

            client = OpenAI(timeout=120)

            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": SUMMERIZER_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": f"""
                                    TARGET LANGUAGE: {lang} \n 
                                    REPOSITORY README : {readme_content} \n 
                                    REPOSITORY DESCRIPTION : {description}
                                    """,
                    },
                ],
            )

            summary = json.loads(response.choices[0].message.content)
            if summary.get("summary"):
                return summary["summary"]

        else:
            client = OpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
            print(model)

            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": SUMMERIZER_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": f"""
                                    TARGET LANGUAGE: {lang} \n 
                                    REPOSITORY README : {readme_content} \n 
                                    REPOSITORY DESCRIPTION : {description}
                                    """,
                    },
                ],
            )

            summary = json.loads(response.choices[0].message.content)
            if summary.get("summary"):
                return summary["summary"]
    except Exception as e:
        logger.debug(e)





def get_final_summary(ranked_repositories, model):
    try:
        if model == "openai":

            client = OpenAI(timeout=120)

            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": MASTER_SUMMERIZER_PROMPT,
                    },
                    {"role": "user", "content": f"""{json.dumps(ranked_repositories)}"""},
                ],
            )

            summary = json.loads(response.choices[0].message.content)
            if summary.get("summary"):
                return summary["summary"]

        else:

            client = OpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
            print(model)


            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": MASTER_SUMMERIZER_PROMPT,
                    },
                    {"role": "user", "content": f"""{json.dumps(ranked_repositories)}"""},
                ],
            )

            summary = json.loads(response.choices[0].message.content)
            if summary.get("summary"):
                return summary["summary"]
    except Exception as e:
        logger.debug(e)