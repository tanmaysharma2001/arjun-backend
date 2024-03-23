import xmltodict
from os import system, path
import json
system("ls")


with open("test.xml", 'r') as f:
    # ls
    xml = f.read()
    data_dict = xmltodict.parse(xml)
    results = data_dict["yandexsearch"]["response"]["results"]["grouping"]["group"]
    for result in results:
        print(result["doc"]["url"])
        print(result["doc"]["title"])
        print(result["doc"].get("headline"))
        print("\n")