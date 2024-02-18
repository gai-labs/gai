from gai.lib.RAGClient import RAGClient
rag = RAGClient()

data = {
    "collection_name":"demo",
    "query_texts":"Who are the young seniors?",
}
response = rag.retrieve(**data)
print(response.json())



