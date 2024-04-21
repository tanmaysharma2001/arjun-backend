from bs4 import BeautifulSoup
import httpx
import os
import threading
import json

with open("osalt.html") as file:
    data = file.read()

    soup = BeautifulSoup(data, "html.parser")

# find all divs with class ".freelancer-card-name-wrapper"
freelancer_card_name_wrappers = soup.find_all("div", class_="w-dyn-item")

tools = []

# create a folder named "ossalt" to store the html files if it does not exist
# if not os.path.exists("ossalt-data"):
    # os.mkdir("ossalt-data")

# folder = os.path.join(os.path.dirname(__file__), "ossalt-data")

def get_data(item, lst):
    with httpx.Client() as client:
        response = client.get(item.pop("url"))
        soup = BeautifulSoup(response.text, "html.parser")
        # with open(f"{folder}/{item['name']}.html", "w") as file:
            # file.write(response.text)
        
        elem = soup.find("div", class_ = "social-link-wrapper-copy")
        for i in elem.find_all("a"):
            if "github" in i["href"]:
                item["github_url"] = i["href"]
                break
        
        elem = soup.find("div", class_="details")
        paragraphs = elem.find_all("p")
        item["license"] = paragraphs[1].text
        item["language"] = paragraphs[3].text
        item["stars"] = paragraphs[5].text
        item["forks"] = paragraphs[7].text
        item["issues"] = paragraphs[9].text
        lst.append(item)
        print(f"Done: {item['name']}")

for i in freelancer_card_name_wrappers:
    name = i.find("h3").text
    alt = i.find("p").text
    alt = alt.replace("Open Source Alternative to", "").strip()
    url = f'https://www.opensourcealternative.to{i.find("a")["href"]}'
    # file.write(f"{name}\t{alt}\n")
    tools.append({"name": name, "alternativeTo": alt, "url": url})

results = []
while tools:
    threads = []
    for i in range(15):
        if tools:
            item = tools.pop()
            thread = threading.Thread(target=get_data, args=(item, results))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()
    
with open("ossalt.json", "w") as file:
    json.dump(results, file, indent=4)