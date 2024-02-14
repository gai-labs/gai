import os
import requests
import json
import gai.common.ConfigHelper as ConfigHelper
from fastapi import WebSocketDisconnect
from gai.common.http_utils import http_post, http_delete,http_get
from gai.common.logging import logging
import asyncio

logger = logging.getLogger(__name__)
lib_config = ConfigHelper.get_lib_config()
base_url = lib_config["gai_url"]

class RAGClient:

    # Provides an updater to get chunk indexing status
    # NOTE: The update is only relevant if this library is used in a FastAPI application with a websocket connection
    async def index_file_async(self, collection_name, file_path, metadata={"source": "unknown"}, progress_updater=None):

        # We will assume file ending with *.pdf to be PDF but this check should be done before the call.
        mode = 'rb' if file_path.endswith('.pdf') else 'r'
        with open(file_path, mode) as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/pdf"),
                "metadata": (None, json.dumps(metadata), "application/json"),
                "collection_name": (None, collection_name, "text/plain")
            }
            url = lib_config["generators"]["rag-index-file"]["url"]
            response = http_post(url=base_url+url, files=files)

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

            return response

    # synchronous version of index_file_async
    def index_file(self, collection_name, file_path, metadata={"source": "unknown"}, progress_updater=None):

        # We will assume file ending with *.pdf to be PDF but this check should be done before the call.
        mode = 'rb' if file_path.endswith('.pdf') else 'r'
        with open(file_path, mode) as f:
            files = {
                "file": (os.path.basename(file_path), f.read(), "application/pdf"),
                "metadata": (None, json.dumps(metadata), "application/json"),
                "collection_name": (None, collection_name, "text/plain")
            }
            url = lib_config["generators"]["rag-index-file"]["url"]
            response = http_post(url=base_url+url, files=files)

        # Callback for progress update (returns a number between 0 and 100)
        if progress_updater:
            # Exception should not disrupt the indexing process
            try:
                # progress = int((i + 1) / len(chunks) * 100)
                progress = 100
                t = asyncio.create_task(progress_updater(progress))
                asyncio.get_event_loop().run_until_complete(t)
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

    def retrieve(self, collection_name, query_texts, n_results=None):
        data = {
            "collection_name": collection_name,
            "query_texts": query_texts
        }
        if n_results:
            data["n_results"] = n_results

        url = lib_config["generators"]["rag-retrieve"]["url"]
        response = http_post(base_url+url, data=data)
        return response

    # Database Management

    def delete_collection(self, collection_name):
        url = lib_config["generators"]["rag-collection"]["url"]
        response = http_delete(f"{base_url}/{url}/{collection_name}")
        return json.loads(response.text)

    def list_collections(self):
        url = lib_config["generators"]["rag-collections"]["url"]
        response = http_get(f"{base_url}/{url}")
        return json.loads(response.text)

    def list_documents(self,collection_name):
        url = lib_config["generators"]["rag-collection"]["url"]
        response = http_get(f"{base_url}/{url}/{collection_name}")
        return json.loads(response.text)
    
    def get_document(self,doc_id):
        url = lib_config["generators"]["rag-document"]["url"]
        response = http_get(f"{base_url}/{url}/{doc_id}")
        return json.loads(response.text)

    def delete_document(self,doc_id):
        url = lib_config["generators"]["rag-document"]["url"]
        response = http_delete(f"{base_url}/{url}/{doc_id}")
        return json.loads(response.text)


