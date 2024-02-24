import os
import json
from fastapi import WebSocketDisconnect
from gai.common.http_utils import http_post_async, http_get_async,http_delete_async
from gai.common.logging import getLogger
from gai.common.errors import ApiException
logger = getLogger(__name__)
from gai.lib.ClientBase import ClientBase

class RAGClientBase(ClientBase):
    
    def __init__(self,config_path=None):
        super().__init__(config_path)
        self.base_url = os.path.join(
            self.config["gai_url"], 
            self.config["generators"]["rag"]["url"].lstrip('/'))
        logger.debug(f'base_url={self.base_url}')

    def _prepare_files_and_metadata(self, collection_name, file_path, metadata):
        mode = 'rb' if file_path.endswith('.pdf') else 'r'
        with open(file_path, mode) as f:
            files = {
                "file": (os.path.basename(file_path), f if mode == 'rb' else f.read(), "application/pdf"),
                "metadata": (None, json.dumps(metadata), "application/json"),
                "collection_name": (None, collection_name, "text/plain")
            }
            return files

class RAGClientAsync(RAGClientBase):

    def __init__(self,config_path=None):
        super().__init__(config_path)

### ----------------- INDEXING ----------------- ###

    # Provides an updater to get chunk indexing status
    # NOTE: The update is only relevant if this library is used in a FastAPI application with a websocket connection
    async def index_file_async(
        self, 
        collection_name, 
        file_path, 
        title="",
        source="",
        authors="",
        publisher="",
        published_date="",
        comments="",
        keywords="", 
        progress_updater=None):
        url=os.path.join(self.base_url,"index-file")
        metadata = {
            "title": title,
            "source": source,
            "authors": authors,
            "publisher": publisher,
            "published_date": published_date,
            "comments": comments,
            "keywords": keywords
        }
       # We will assume file ending with *.pdf to be PDF but this check should be done before the call.
        mode = 'rb' if file_path.endswith('.pdf') else 'r'
        with open(file_path, mode) as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/pdf"),
                "metadata": (None, json.dumps(metadata), "application/json"),
                "collection_name": (None, collection_name, "text/plain")
            }
            response = await http_post_async(url=url, files=files)

        # Callback for progress update (returns a number between 0 and 100)
        if progress_updater:
            # Exception should not disrupt the indexing process
            try:
                # progress = int((i + 1) / len(chunks) * 100)
                progress = 100
                await progress_updater(progress)
                logger.debug(
                    f"RAGClient: progress={progress}")
                # await send_progress(websocket, progress)
            except WebSocketDisconnect as e:
                if e.code == 1000:
                    # Normal closure, perhaps log it as info and continue gracefully
                    logger.info(
                        f"RAGClient: WebSocket closed normally with code {e.code}")
                    pass
                else:
                    # Handle other codes as actual errors
                    logger.error(
                        f"RAGClient: WebSocket disconnected with error code {e.code}")
                    pass
            except Exception as e:
                logger.error(
                    f"RetrievalGeneration.index_async: Update websocket progress failed. Error={str(e)}")
                pass

        return json.loads(response.text)


    async def retrieve_async(self, collection_name, query_texts, n_results=None):
        url = os.path.join(self.base_url,"retrieve")
        data = {
            "collection_name": collection_name,
            "query_texts": query_texts
        }
        if n_results:
            data["n_results"] = n_results

        response = await http_post_async(url, data=data)
        return response

    # Database Management

    async def delete_collection_async(self, collection_name):
        url = os.path.join(self.base_url,"collection",collection_name)
        logger.info(f"RAGClient.delete_collection: Deleting collection {url}")
        try:
            response = await http_delete_async(url)
        except ApiException as e:
            if e.code == 'collection_not_found':
                return {"count":0}
            logger.error(e)
            raise e
        return json.loads(response.text)

    async def list_collections(self):
        url = os.path.join(self.base_url,"collections")
        response = await http_get_async(url)
        return json.loads(response.text)

    async def list_documents(self,collection_name):
        url = os.path.join(self.base_url,"collection",collection_name)
        response = await http_get_async(url)
        return json.loads(response.text)
    
    async def get_document_async(self,collection_name,doc_id):
        url = os.path.join(self.base_url,f"document/{collection_name}/{doc_id}")
        response = await http_get_async(url)
        return json.loads(response.text)

    async def delete_document_async(self,collection_name,doc_id):
        url = os.path.join(self.base_url,f"document/{collection_name}/{doc_id}")
        response = await http_delete_async(url)
        return json.loads(response.text)

