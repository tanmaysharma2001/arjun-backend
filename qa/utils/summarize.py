import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import MASTER_SUMMERIZER_PROMPT, SUMMERIZER_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]


async def summarize(lang, readme_content, description, model):

    if model == "openai":
        
        client = AsyncOpenAI(timeout=10)

        response = await client.chat.completions.create(
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
        return summary["summary"]

    else:
        client = AsyncOpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        print(model)

        response = await client.chat.completions.create(
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
        return summary["summary"]




async def get_final_summary(ranked_repositories, model):
    if model == "openai":

        client = AsyncOpenAI(timeout=10)

        response = await client.chat.completions.create(
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
        return summary["summary"]
    
    else:


        client = AsyncOpenAI(base_url = 'https://ai.pptx704.com',api_key='ollama',timeout=120)
        print(model)


        response = await client.chat.completions.create(
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
        return summary["summary"]