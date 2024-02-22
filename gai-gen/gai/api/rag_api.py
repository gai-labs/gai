import uuid
from gai.common.errors import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError as SqlAlchemyIntegrityError
from sqlite3 import IntegrityError as Sqlite3IntegrityError

from fastapi import FastAPI, Body, Form, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

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
from gai.common import file_utils

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

gen = Gaigen.GetInstance()

# Pre-load default model

def preload_model():
    try:
        # RAG does not use "default" model
        gen.load("rag")
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

            # Give the path to the file to the RAG
            metadata_dict = json.loads(metadata)
            doc_id = await gen.index_async(
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
            raise HTTPException(409,{
                "code": "duplicate_document",
                "message": "Document already exists in the database.",
                "url": "/gen/v1/rag/index-file"
            })
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
        result = gen.retrieve(collection_name=request.collection_name,
                              query_texts=request.query_texts, n_results=request.n_results)
        logger.debug("main.retrieve=", result)
        return result
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.retrieve: {id} {str(e)}")
        raise InternalException(id)

### ----------------- DOCUMENTS ----------------- ###
# Check if the content of a document exists in the collection
# POST /gen/v1/rag/collection/{collection_name}/document_exists
@app.post("/gen/v1/rag/collection/{collection_name}/document_exists")
async def document_exists(collection_name, file: UploadFile = File(...)):
    try:
        text = await file.read()
        text = text.decode("utf-8")
        exists = RAG.Exists(collection_name=collection_name, text=text)
        return JSONResponse(status_code=200, content={
            "exists": exists
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.document_exists: {id} {str(e)}")
        raise InternalException(id)

# Helper function to split a document into chunks
# POST /gen/v1/rag/document/split
@app.post("/gen/v1/rag/document/split")
async def document_split(file: UploadFile = File(...)):
    try:
        text = await file.read()
        chunks_dir = file_utils.split_text(text=text.decode('utf-8'),chunk_size=1000,chunk_overlap=100)
        chunks = os.listdir(chunks_dir)
        result=[]
        for chunk in chunks:
            with open(os.path.join(chunks_dir, chunk), 'r') as f:
                content = f.read()
            result.append(content)
        return JSONResponse(status_code=200, content={
            "chunks": result
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.document_split: {id} {str(e)}")
        raise InternalException(id)

### ----------------- COLLECTIONS ----------------- ###

# DELETE /gen/v1/rag/collection/{}
@app.delete("/gen/v1/rag/collection/{collection_name}")
async def delete_collection(collection_name):
    try:
        if collection_name not in [collection.name for collection in RAG.list_collections()]:
            logger.warning(f"rag_api.delete_collection: Collection with name={collection_name} not found.")
            # Bypass the error handler and return a 404 directly            
            return JSONResponse(status_code=404, content={
                "type": "error", 
                "code": "collection_not_found", 
                "message": "The specified collection does not exist."
            })

        RAG.delete_collection(collection_name=collection_name)
        after = RAG.list_collections()
        return JSONResponse(status_code=200, content={
            "count": len(after)
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.delete_collection: {id} {str(e)}")
        raise InternalException(id)

# GET /gen/v1/rag/collections
@app.get("/gen/v1/rag/collections")
async def list_collections():
    try:
        collections = [collection.name for collection in RAG.list_collections()]
        return JSONResponse(status_code=200, content={
            "collections": collections
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.list_collections: {id} {str(e)}")
        raise InternalException(id)

### ----------------- DOCUMENTS ----------------- ###

# GET /gen/v1/rag/collection/{collection_name}
@app.get("/gen/v1/rag/collection/{collection_name}")
async def list_documents_in_collection(collection_name):
    try:
        docs = RAG.list_documents(collection_name=collection_name)
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
async def list_all_documents():
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
@app.get("/gen/v1/rag/document/{document_id}")
async def get_document(document_id):
    try:
        document = RAG.get_document(document_id=document_id)
        if document is None:
            logger.warning(f"rag_api.get_documents: Document with Id={document_id} not found.")
            # Bypass the error handler and return a 404 directly
            return JSONResponse(status_code=404, content={
                "type": "error", 
                "code": "document_not_found", 
                "message": f"Document with Id={document_id} not found."
            })

        return JSONResponse(status_code=200, content={
            "document": jsonable_encoder(document)
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.get_document: {id} {str(e)}")
        raise InternalException(id)

# POST /gen/v1/rag/document
class UpdateDocumentRequest(BaseModel):
    Id: str
    FileName: str = None
    Source: str = None
    Abstract: str = None
    Authors: str = None
    Title: str = None
    Publisher: str = None
    PublishedDate: str = None
    Comments: str = None
@app.post("/gen/v1/rag/document")
async def update_document(req: UpdateDocumentRequest = Body(...)):
    try:
        doc = RAG.get_document(document_id=req.Id)
        if doc is None:
            logger.warning(f"Document with Id={req.Id} not found.")
            # Bypass the error handler and return a 404 directly
            return JSONResponse(status_code=404, content={
                "type": "error", 
                "code": "document_not_found", 
                "message": f"Document with Id={req.Id} not found."
            })
                
        updated_doc = RAG.update_document(document=req)
        return JSONResponse(status_code=200, content={
            "message": "Document updated successfully",
            "document": updated_doc
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.update_document: {id} {str(e)}")
        raise InternalException(id)

# DELETE /gen/v1/rag/document/{document_id}
@app.delete("/gen/v1/rag/document/{document_id}")
async def delete_document(document_id):
    try:
        doc = RAG.get_document(document_id=document_id)
        if doc is None:
            logger.warning(f"Document with Id={document_id} not found.")
            # Bypass the error handler and return a 404 directly
            return JSONResponse(status_code=404, content={
                "type": "error", 
                "code": "document_not_found", 
                "message": f"Document with Id={document_id} not found."
            })
        
        RAG.delete_document(document_id=document_id)
        return JSONResponse(status_code=200, content={
            "message": f"Document with id {document_id} deleted successfully"
        })
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"rag_api.delete_document: {id} {str(e)}")
        raise InternalException(id)

### ----------------- CHUNKS ----------------- ###

@app.get("/gen/v1/rag/chunks")
async def list_chunks():
    row_chunks = []
    collections = RAG.list_collections()
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

@app.get("/gen/v1/rag/chunks/{collection_name}")
async def list_chunks(collection_name: str):
    row_chunks = []
    collection = RAG.get_collection(collection_name)
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

@app.get("/gen/v1/rag/chunk/{id}")
async def get_chunk(id):
    collections = RAG.list_collections()
    if not collections:
        return "No collections found"
    collection = collections[0]
    chunk = collection.get(ids=[id])
    return chunk

@app.delete("/gen/v1/rag/chunk/{collection_name}/{chunk_id}")
async def delete_chunk(collection_name:str, chunk_id:str):
    RAG.get_collection(collection_name).delete(ids=[chunk_id])

@app.delete("/gen/v1/rag/chunks/{collection_name}")
async def delete_chunk(collection_name:str):
    ids=RAG.get_collection(collection_name).get()["ids"]
    RAG.get_collection(collection_name).delete(ids=ids)






# -----------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12031)
