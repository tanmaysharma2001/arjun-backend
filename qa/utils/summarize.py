import os
import json
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import SUMMERIZER_PROMPT

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]


async def summerize(lang, readme_content, description):
    client = AsyncOpenAI()

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
                "content": f"""TARGET LANGUAGE: {lang} \n 
  REPOSITORY README : {readme_content} \n 
  REPOSITORY DESCRIPTION : {description}""",
            },
        ],
    )

    summary = json.loads(response.choices[0].message.content)
    print(summary)
    return summary["summary"]
