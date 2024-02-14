from gai.lib.GGG import GGG
ggg = GGG()

print("Index...")
data = {
    "collection_name": "demo",
    "file_path": "../lib/rag/pm_long_speech_2023.txt",
    "metadata": {"title": "2023 National Day Rally Speech", "source": "https://www.pmo.gov.sg/Newsroom/national-day-rally-2023"},
}
response = ggg("index", **data)
print(response.json())
print("Index...done.")

print("Retrieving...")
data = {
    "collection_name": "demo",
    "query_texts": "Who are the young seniors?",
}
response = ggg("retrieve", **data)
print(response.json())
print("Retrieving...done.")
