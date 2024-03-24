import supabase
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = supabase.create_client(supabase_url, supabase_key)

def add_repo_to_db(data: dict) -> None:
    supabase.table('repositories').insert({
        "name": data["name"],
        "version_control": data["version_control"],
        "url": data["url"],
        "forks": data["forks"],
        "stars": data["stars"],
        "description": data["description"],
        "readme_content": data["readme_content"],
        # "summary": "abcd" #data["summary"]
    }).execute()