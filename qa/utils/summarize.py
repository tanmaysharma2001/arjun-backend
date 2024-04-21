import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import MASTER_SUMMERIZER_PROMPT, SUMMERIZER_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]


async def summarize(lang, readme_content, description):
    client = AsyncOpenAI(timeout=10)

    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
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
    # print(summary)
    return summary["summary"]


async def get_final_summary(ranked_repositories):
    client = AsyncOpenAI(timeout=10, max_retries=5)

    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
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
    # print(summary)
    return summary["summary"]