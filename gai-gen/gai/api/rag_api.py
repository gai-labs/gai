import uuid
from gai.common.errors import *
from fastapi import FastAPI, Body, Form, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from gai.gen.rag.models.IndexedDocumentChunkPydantic import IndexedDocumentChunkPydantic

import dependencies
import tempfile
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()
import os
import json
import tempfile

from gai.api.globals import status_updater
from gai.api.status_update_router import status_update_router
from gai.gen.rag import RAG
from gai.gen import Gaigen
from gai.common.errors import *
from gai.common import file_utils,utils
from gai.gen.rag import RAG
import shutil

# Configure Dependencies
dependencies.configure_logging()
from gai.common.logging import getLogger
logger = getLogger(__name__)
logger.info(f"Starting Gai Generators Service v{dependencies.APP_VERSION}")
logger.info(f"Version of gai_gen installed = {dependencies.LIB_VERSION}")
swagger_url = dependencies.get_swagger_url()
app = FastAPI(
    title="Gai Generators Service",
    description="""Gai Generators Service""",
    version=dependencies.APP_VERSION,
    docs_url=swagger_url
)
dependencies.configure_cors(app)
semaphore = dependencies.configure_semaphore()

# Add status update router
app.include_router(status_update_router)

from dotenv import load_dotenv
load_dotenv()
from gai.common.logging import getLogger
logger = getLogger(__name__)
in_memory = os.environ.get("IN_MEMORY",True).lower() != "false"
rag = RAG(in_memory=in_memory)

# Pre-load default model

def preload_model():
    try:
        # RAG does not use "default" model
        rag.load()
    except Exception as e:
        logger.error(f"Failed to preload default model: {e}")
        raise e


preload_model()

# RAG specific

### ----------------- INDEXING ----------------- ###

# POST /gen/v1/rag/index-file
@app.post("/gen/v1/rag/index-file")
async def index_file(collection_name: str = Form(...), file: UploadFile = File(...), metadata: str = Form(...)):
    try:
        # Save the file to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_location = os.path.join(temp_dir, file.filename)
            with open(file_location, "wb+") as file_object:
                content = await file.read()  # Read the content of the uploaded file
                file_object.write(content)

            # Give the temp file path to the RAG
            metadata_dict = json.loads(metadata)
            doc_id = await rag.index_async(
                collection_name=collection_name,
                file_path=file_location,
                file_type=file.filename.split(".")[-1],
                title=metadata_dict.get("title", ""),
                source=metadata_dict.get("source", ""),
                authors=metadata_dict.get("authors", ""),
                publisher=metadata_dict.get("publisher", ""),
                published_date=metadata_dict.get("publishedDate", ""),
                comments=metadata_dict.get("comments", ""),
                keywords=metadata_dict.get("keywords", ""),
                status_updater=status_updater)

            return JSONResponse(status_code=200, content={
                "document_id": doc_id
            })
    except Exception as e:
        if "Document already exists in the database" in str(e):
            raise DuplicatedDocumentException()
        id = str(uuid.uuid4())
        logger.error(f"rag_api.index_file: {id} {str(e)}")
        raise InternalException(id)

### ----------------- RETRIEVAL ----------------- ###

# Retrieve document chunks using semantic search
# POST /gen/v1/rag/retrieve
class QueryRequest(BaseModel):
    collection_name: str
    query_texts: str
    n_results: int = 3
@app.post("/gen/v1/rag/retrieve")
async def retrieve(request: QueryRequest = Body(...)):
    try:
        logger.info(
            f"main.retrieve: collection_name={request.collection_name}")
        result = rag.retrieve(collection_name=request.collection_name,
                              query_texts=request.query_texts, n_results=request.n_results)
        logger.debug("main.retrieve=", result)
        return result
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.retrieve: {id} {str(e)}")
        raise InternalException(id)


### ----------------- COLLECTIONS ----------------- ###

# DELETE /gen/v1/rag/collection/{}
@app.delete("/gen/v1/rag/collection/{collection_name}")
async def delete_collection(collection_name):
    try:
        if collection_name not in [collection.name for collection in rag.list_collections()]:
            logger.warning(f"rag_api.delete_collection: Collection with name={collection_name} not found.")
            raise CollectionNotFoundException(collection_name)

        rag.delete_collection(collection_name=collection_name)
        after = rag.list_collections()
        return JSONResponse(status_code=200, content={
            "count": len(after)
        })
    except CollectionNotFoundException as e:
        raise e
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.delete_collection: {id} {str(e)}")
        raise InternalException(id)

# GET /gen/v1/rag/collections
@app.get("/gen/v1/rag/collections")
async def list_collections():
    try:
        collections = [collection.name for collection in rag.list_collections()]
        return JSONResponse(status_code=200, content={
            "collections": collections
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.list_collections: {id} {str(e)}")
        raise InternalException(id)
    
# DELETE /gen/v1/rag/purge
@app.delete("/gen/v1/rag/purge")
async def purge_all():
    try:
        app_path = utils.get_app_path()
        # Delete chromadb file
        chromdb_dir = os.path.join(app_path, 'chromedb')
        shutil.rmtree(chromdb_dir, ignore_errors=True)

        # Delete db file
        sqlite_file = os.path.join(app_path, 'gai-rag.db')
        os.chmod(sqlite_file, 0o777)
        os.remove(sqlite_file)

    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.purge_all: {id} {str(e)}")
        raise InternalException(id)

### ------------------------------------------------------------------------------- DOCUMENTS ------------------------------------------------------------------------------------ ###

# Check if document already exists
# POST /gen/v1/rag/collection/{collection_name}/document_exists
@app.post("/gen/v1/rag/collection/{collection_name}/document_exists")
async def document_exists(collection_name, file: UploadFile = File(...)):
    try:
        
        # Save the file to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_location = os.path.join(temp_dir, file.filename)
            with open(file_location, "wb+") as file_object:
                content = await file.read()  # Read the content of the uploaded file
                file_object.write(content)

        doc_id = rag.create_document_hash(file_location)
        doc = rag.get_document(collection_name, document_id=doc_id)
        return JSONResponse(status_code=200, content={
            "exists": doc is not None
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.document_exists: {id} {str(e)}")
        raise InternalException(id)


# GET /gen/v1/rag/collection/{collection_name}
@app.get("/gen/v1/rag/collection/{collection_name}")
@app.get("/gen/v1/rag/documents/{collection_name}")
async def list_documents_by_collection(collection_name):
    try:
        docs = rag.list_documents(collection_name=collection_name)
        formatted = [{"id":doc.Id,"title":doc.Title,"size":doc.ByteSize,"chunk_count":doc.ChunkCount,"chunk_size":doc.ChunkSize,"overlap_size":doc.Overlap,"source":doc.Source} for doc in docs]
        return JSONResponse(status_code=200, content={
            "documents": formatted
        })        
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.list_documents: {id} {str(e)}")
        raise InternalException(id)

# GET /gen/v1/rag/documents
@app.get("/gen/v1/rag/documents")
async def list_documents():
    try:
        docs = RAG.list_documents()
        formatted = [{"id":doc.Id,"title":doc.Title,"size":doc.ByteSize,"chunk_count":doc.ChunkCount,"chunk_size":doc.ChunkSize,"overlap_size":doc.Overlap,"source":doc.Source} for doc in docs]
        return JSONResponse(status_code=200, content={
            "documents": formatted
        })        
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.list_documents: {id} {str(e)}")
        raise InternalException(id)

# GET /gen/v1/rag/document/{document_id}
@app.get("/gen/v1/rag/document/{collection_name}/{document_id}")
async def get_document(collection_name, document_id):
    try:
        document = rag.get_document(collection_name=collection_name, document_id=document_id)
        if document is None:
            logger.warning(f"rag_api.get_documents: Document with Id={document_id} not found.")
            raise DocumentNotFoundException(document_id)

        return JSONResponse(status_code=200, content={
            "document": jsonable_encoder(document)
        })
    except DocumentNotFoundException as e:
        raise e
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.get_document: {id} {str(e)}")
        raise InternalException(id)

# POST /gen/v1/rag/document
class UpdateDocumentRequest(BaseModel):
    FileName: str = None
    Source: str = None
    Abstract: str = None
    Authors: str = None
    Title: str = None
    Publisher: str = None
    PublishedDate: str = None
    Comments: str = None
@app.post("/gen/v1/rag/document/{collection_name}/{document_id}")
async def update_document(collection_name, document_id, req: UpdateDocumentRequest = Body(...)):
    try:
        doc = rag.get_document(collection_name=collection_name, document_id=document_id)
        if doc is None:
            logger.warning(f"Document with Id={req.Id} not found.")
            # Bypass the error handler and return a 404 directly
            raise DocumentNotFoundException(req.Id)
                
        updated_doc = rag.update_document(collection_name=collection_name, document_id=document_id, document=req)
        return JSONResponse(status_code=200, content={
            "message": "Document updated successfully",
            "document": updated_doc
        })
    except DocumentNotFoundException as e:
        raise e
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.update_document: {id} {str(e)}")
        raise InternalException(id)

# DELETE /gen/v1/rag/document/{document_id}
@app.delete("/gen/v1/rag/document/{collection_name}/{document_id}")
async def delete_document(collection_name, document_id):
    try:
        doc = rag.get_document(collection_name=collection_name, document_id=document_id)
        if doc is None:
            logger.warning(f"Document with Id={document_id} not found.")
            raise DocumentNotFoundException(document_id)
        
        rag.delete_document(collection_name=collection_name, document_id=document_id)
        return JSONResponse(status_code=200, content={
            "message": f"Document with id {document_id} deleted successfully"
        })
    except DocumentNotFoundException as e:
        raise e
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.delete_document: {id} {str(e)}")
        raise InternalException(id)

### ----------------- CHUNKS ----------------- ###

@app.get("/gen/v1/rag/chunks")
async def list_chunks():
    row_chunks = []
    collections = rag.list_collections()
    if not collections:
        return "No collections found"
    for collection in collections:
        columns = collection.get()
        for i in range(len(columns['ids'])):
            cell = {
                'id': columns["ids"][i],
                'documents': columns["documents"][i],
            }
            row_chunks.append(cell)
    return row_chunks

@app.get("/gen/v1/rag/chunks/by_collection/{collection_name}")
async def list_chunks_by_collection(collection_name: str):
    row_chunks = []
    collection = rag.get_collection(collection_name)
    if not collection:
        return "Collection not found"
    columns = collection.get()
    for i in range(len(columns['ids'])):
        cell = {
            'id': columns["ids"][i],
            'documents': columns["documents"][i],
        }
        row_chunks.append(cell)
    return row_chunks

@app.get("/gen/v1/rag/chunks/by_document/{collection_name}/{document_id}")
async def list_chunks_by_document(collection_name, document_id: str):
    chunks = []
    doc = rag.get_document(document_id)
    if not doc:
        return "Document not found"
    for chunk in doc.get_chunks():
        chunks.append(IndexedDocumentChunkPydantic(**chunk))
    return chunks


@app.get("/gen/v1/rag/chunk/{id}")
async def get_chunk(id):
    collections = rag.list_collections()
    if not collections:
        return "No collections found"
    collection = collections[0]
    chunk = collection.get(ids=[id])
    return chunk

@app.delete("/gen/v1/rag/chunk/{collection_name}/{chunk_id}")
async def delete_chunk(collection_name:str, chunk_id:str):
    rag.delete_chunk(collection_name, chunk_id)

@app.delete("/gen/v1/rag/chunks/{collection_name}")
async def delete_chunks(collection_name:str):
    chunks = rag.list_chunks_by_collection_name(collection_name)
    for chunk in chunks:
        rag.delete_chunk(collection_name, chunk['id'])

# -----------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12031)
