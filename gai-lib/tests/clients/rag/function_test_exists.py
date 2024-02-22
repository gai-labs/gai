from gai.lib.RAGClient import RAGClient
rag = RAGClient()
file_path = "./pm_long_speech_2023.txt"
collection_name = "demo"
print(rag.exists("demo",file_path))


