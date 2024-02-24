from gai.lib.RAGClient import RAGClient
import asyncio

rag = RAGClient()

asyncio.run(rag.index_file_async(
    file_path="./tests/lib/rag/attention-is-all-you-need-1706.03762.pdf",
    collection_name="demo",
    metadata={"title": "Attention is all you need",
              "author": "Vaswani et al."}
))
